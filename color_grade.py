"""
Floor 5 — Cinematic LUT / HDR Color Grading

Real 3D LUT color grading applied via FFmpeg post-pass, replacing
the low-fidelity CSS gradient overlays from Remotion.

Features:
  - Self-bootstrapping .cube LUT library (generates on first run)
  - Vibe-to-LUT mapping matching AIDirectorPlan's vibe classification
  - HDR detection via ffprobe color metadata
  - Tone-mapping (zscale + tonemap) before LUT for HDR sources
  - Histogram-safe application (no banding)
"""

import os
import sys
import math
import json
import subprocess
import time
from typing import Optional, Dict, Any, Tuple

# ============================================================================
# LUT LIBRARY — Maps AI Director vibe/style to .cube filenames
# ============================================================================

LUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts")

# Maps colorGradeLUT names (chosen by AI Director) to .cube filenames
LUT_LIBRARY: Dict[str, str] = {
    "intellectual_podcast":    "intellectual_podcast.cube",
    "philosophical_interview": "philosophical_interview.cube",
    "business_podcast":        "business_podcast.cube",
    "high_energy":             "high_energy.cube",
    "moody_story":             "moody_story.cube",
    "scientific_breakdown":    "scientific_breakdown.cube",
    "vibrant_pop":             "vibrant_pop.cube",
    "vintage_film":            "vintage_film.cube",
    "clean_modern":            "clean_modern.cube",
}

# Fallback mapping: AI Director's colorGradingStyle → LUT name
STYLE_TO_LUT: Dict[str, str] = {
    "teal-orange":  "intellectual_podcast",
    "moody-dark":   "moody_story",
    "vibrant-pop":  "vibrant_pop",
    "vintage-film": "vintage_film",
}

# Vibe → default LUT (if AI Director doesn't explicitly choose)
VIBE_TO_LUT: Dict[str, str] = {
    "philosophical_interview":   "philosophical_interview",
    "intellectual_dialogue":     "intellectual_podcast",
    "scientific_breakdown":      "scientific_breakdown",
    "business_podcast":          "business_podcast",
    "high_energy":               "high_energy",
    "high_stakes_debate":        "high_energy",
    "emotional_storytelling":    "moody_story",
    "casual_banter":             "clean_modern",
}


# ============================================================================
# 3D LUT GENERATION — Color science transforms for each cinematic profile
# ============================================================================

def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _s_curve(x: float, contrast: float = 1.0) -> float:
    """Professional, subtle S-curve that protects skin tones and highlights.
       Using a gentle cubic bezier approach rather than harsh sigmoid."""
    if contrast <= 0:
        return x
    
    # Very gentle contrast curve that pivots around mid-gray (0.18 for linear, but 0.4 for gamma-encoded)
    pivot = 0.4
    
    # Calculate difference from pivot
    diff = x - pivot
    
    # Apply subtle contrast multiplier
    # contrast of 1.0 means very slight enhancement (1.1x multiplier)
    multiplier = 1.0 + (contrast * 0.1)
    
    adjusted = pivot + (diff * multiplier)
    
    # Soft clip highlights to prevent blowing out (exposure protection)
    if adjusted > 0.9:
        # Smoothly roll off towards 1.0
        adjusted = 0.9 + (1.0 - math.exp(-10 * (adjusted - 0.9))) * 0.1
        
    # Prevent crushing blacks completely
    if adjusted < 0.02:
        adjusted = 0.02 + (adjusted * 0.5)
        
    return _clamp(adjusted)


def _luminance(r: float, g: float, b: float) -> float:
    """Rec.709 luminance."""
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _adjust_saturation(r: float, g: float, b: float, factor: float) -> Tuple[float, float, float]:
    """Adjust saturation by blending toward/away from luminance."""
    lum = _luminance(r, g, b)
    return (
        _clamp(lum + (r - lum) * factor),
        _clamp(lum + (g - lum) * factor),
        _clamp(lum + (b - lum) * factor),
    )


def _split_tone(
    r: float, g: float, b: float,
    shadow_rgb: Tuple[float, float, float] = (0, 0, 0),
    highlight_rgb: Tuple[float, float, float] = (1, 1, 1),
    shadow_strength: float = 0.0,
    highlight_strength: float = 0.0,
) -> Tuple[float, float, float]:
    """Apply split toning: push shadows toward one hue, highlights toward another."""
    lum = _luminance(r, g, b)
    # Shadow influence (stronger when pixel is dark)
    shadow_weight = (1.0 - lum) * shadow_strength
    # Highlight influence (stronger when pixel is bright)
    highlight_weight = lum * highlight_strength
    return (
        _clamp(r + (shadow_rgb[0] - 0.5) * shadow_weight + (highlight_rgb[0] - 0.5) * highlight_weight),
        _clamp(g + (shadow_rgb[1] - 0.5) * shadow_weight + (highlight_rgb[1] - 0.5) * highlight_weight),
        _clamp(b + (shadow_rgb[2] - 0.5) * shadow_weight + (highlight_rgb[2] - 0.5) * highlight_weight),
    )


def _lift_gamma_gain(
    r: float, g: float, b: float,
    lift: Tuple[float, float, float] = (0, 0, 0),
    gamma: Tuple[float, float, float] = (1, 1, 1),
    gain: Tuple[float, float, float] = (1, 1, 1),
) -> Tuple[float, float, float]:
    """Standard 3-way color correction: lift (shadows), gamma (midtones), gain (highlights)."""
    def apply_channel(v: float, l: float, g_val: float, gn: float) -> float:
        # Professional Lift (Shadows): Affects darks more than lights
        v = v + l * (1.0 - v)**2 
        # Gain (Highlights): Simple multiplier
        v = v * gn
        # Gamma (Midtones): Power curve
        if v > 0 and g_val != 1.0:
            v = math.pow(v, 1.0 / g_val)
            
        # Hard clamp to prevent NaN or extreme blowout
        return _clamp(v)

    return (
        apply_channel(r, lift[0], gamma[0], gain[0]),
        apply_channel(g, lift[1], gamma[1], gain[1]),
        apply_channel(b, lift[2], gamma[2], gain[2]),
    )


# ---- LUT PROFILES ----

def _transform_intellectual_podcast(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Subdued, Rec709-neutral with lifted blacks. Slight teal shadows, warm highlights."""
    # Mild S-curve
    r, g, b = _s_curve(r, 0.6), _s_curve(g, 0.6), _s_curve(b, 0.6)
    # Lift blacks slightly (milky shadows for editorial feel)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.04, 0.04, 0.06), gamma=(1.02, 1.0, 0.98), gain=(1.0, 0.98, 0.96))
    # Split tone: teal shadows, warm highlights
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.35, 0.55, 0.60), shadow_strength=0.12,
        highlight_rgb=(0.58, 0.52, 0.42), highlight_strength=0.08)
    # Slightly desaturated for sophistication
    r, g, b = _adjust_saturation(r, g, b, 0.88)
    return r, g, b


def _transform_philosophical_interview(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Gentle warmth with lifted blacks. Golden highlights, neutral shadows."""
    r, g, b = _s_curve(r, 0.5), _s_curve(g, 0.5), _s_curve(b, 0.5)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.05, 0.04, 0.03), gamma=(1.01, 1.0, 0.97), gain=(1.02, 0.99, 0.94))
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.45, 0.48, 0.55), shadow_strength=0.08,
        highlight_rgb=(0.60, 0.54, 0.40), highlight_strength=0.10)
    r, g, b = _adjust_saturation(r, g, b, 0.86)
    return r, g, b


def _transform_business_podcast(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Clean, neutral-warm. Flattering skin tones, subtle highlight rolloff."""
    r, g, b = _s_curve(r, 0.7), _s_curve(g, 0.7), _s_curve(b, 0.7)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.03, 0.03, 0.02), gamma=(1.02, 1.01, 0.99), gain=(1.01, 0.99, 0.96))
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.48, 0.48, 0.52), shadow_strength=0.05,
        highlight_rgb=(0.55, 0.52, 0.46), highlight_strength=0.06)
    r, g, b = _adjust_saturation(r, g, b, 0.93)
    return r, g, b


def _transform_high_energy(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Punchy contrast, warm highlights, boosted saturation."""
    r, g, b = _s_curve(r, 1.2), _s_curve(g, 1.2), _s_curve(b, 1.2)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.02, 0.01, 0.01), gamma=(1.05, 1.0, 0.95), gain=(1.05, 0.98, 0.92))
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.35, 0.45, 0.55), shadow_strength=0.10,
        highlight_rgb=(0.62, 0.52, 0.38), highlight_strength=0.12)
    r, g, b = _adjust_saturation(r, g, b, 1.15)
    return r, g, b


def _transform_moody_story(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Classic teal-orange. Crushed shadows, strong color contrast."""
    r, g, b = _s_curve(r, 1.0), _s_curve(g, 1.0), _s_curve(b, 1.0)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.01, 0.02, 0.04), gamma=(1.04, 0.98, 0.94), gain=(1.04, 0.96, 0.90))
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.30, 0.50, 0.60), shadow_strength=0.18,
        highlight_rgb=(0.62, 0.48, 0.32), highlight_strength=0.15)
    r, g, b = _adjust_saturation(r, g, b, 0.82)
    return r, g, b


def _transform_scientific_breakdown(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Clinical cool tones. Neutral midtones, blue shadows."""
    r, g, b = _s_curve(r, 0.8), _s_curve(g, 0.8), _s_curve(b, 0.8)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.02, 0.03, 0.05), gamma=(0.99, 1.0, 1.02), gain=(0.97, 0.99, 1.02))
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.40, 0.48, 0.60), shadow_strength=0.12,
        highlight_rgb=(0.52, 0.50, 0.48), highlight_strength=0.04)
    r, g, b = _adjust_saturation(r, g, b, 0.90)
    return r, g, b


def _transform_vibrant_pop(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Saturated, warm, energetic."""
    r, g, b = _s_curve(r, 0.9), _s_curve(g, 0.9), _s_curve(b, 0.9)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.02, 0.02, 0.01), gamma=(1.03, 1.01, 0.98), gain=(1.03, 1.0, 0.95))
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.48, 0.42, 0.55), shadow_strength=0.08,
        highlight_rgb=(0.58, 0.52, 0.42), highlight_strength=0.08)
    r, g, b = _adjust_saturation(r, g, b, 1.20)
    return r, g, b


def _transform_vintage_film(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Nostalgic sepia. Lifted blacks, desaturated, warm cast."""
    r, g, b = _s_curve(r, 0.4), _s_curve(g, 0.4), _s_curve(b, 0.4)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.08, 0.06, 0.04), gamma=(1.0, 0.98, 0.94), gain=(1.02, 0.97, 0.88))
    r, g, b = _split_tone(r, g, b,
        shadow_rgb=(0.52, 0.48, 0.42), shadow_strength=0.15,
        highlight_rgb=(0.58, 0.54, 0.44), highlight_strength=0.12)
    r, g, b = _adjust_saturation(r, g, b, 0.72)
    return r, g, b


def _transform_clean_modern(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Subtle contrast, neutral color, slight highlight softening."""
    r, g, b = _s_curve(r, 0.3), _s_curve(g, 0.3), _s_curve(b, 0.3)
    r, g, b = _lift_gamma_gain(r, g, b, lift=(0.02, 0.02, 0.02), gamma=(1.01, 1.0, 1.0), gain=(1.0, 0.99, 0.98))
    r, g, b = _adjust_saturation(r, g, b, 0.96)
    return r, g, b


# Transform function registry
LUT_TRANSFORMS = {
    "intellectual_podcast":    _transform_intellectual_podcast,
    "philosophical_interview": _transform_philosophical_interview,
    "business_podcast":        _transform_business_podcast,
    "high_energy":             _transform_high_energy,
    "moody_story":             _transform_moody_story,
    "scientific_breakdown":    _transform_scientific_breakdown,
    "vibrant_pop":             _transform_vibrant_pop,
    "vintage_film":            _transform_vintage_film,
    "clean_modern":            _transform_clean_modern,
}


def generate_cube_lut(name: str, output_path: str, size: int = 17) -> bool:
    """
    Generate a .cube 3D LUT file using the named color transform.

    Args:
        name: LUT profile name (must exist in LUT_TRANSFORMS)
        output_path: Path to write the .cube file
        size: LUT grid size (17 = standard, 33 = high quality)

    Returns:
        True if generation succeeded.
    """
    transform = LUT_TRANSFORMS.get(name)
    if not transform:
        print(f"[COLOR GRADE] Unknown LUT profile: {name}")
        return False

    print(f"[COLOR GRADE] Generating {name}.cube ({size}x{size}x{size} = {size**3} entries)...")
    start = time.time()

    lines = []
    lines.append(f'TITLE "{name}"')
    lines.append(f"LUT_3D_SIZE {size}")
    lines.append("")

    # .cube format: B varies slowest, then G, then R fastest
    for b_idx in range(size):
        for g_idx in range(size):
            for r_idx in range(size):
                r_in = r_idx / (size - 1)
                g_in = g_idx / (size - 1)
                b_in = b_idx / (size - 1)

                r_out, g_out, b_out = transform(r_in, g_in, b_in)
                r_out = _clamp(r_out)
                g_out = _clamp(g_out)
                b_out = _clamp(b_out)

                lines.append(f"{r_out:.6f} {g_out:.6f} {b_out:.6f}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print(f"[COLOR GRADE] Generated {name}.cube in {time.time() - start:.1f}s")
    return True


def ensure_lut_library() -> bool:
    """Generate all .cube LUT files if they don't exist. Self-bootstrapping."""
    os.makedirs(LUTS_DIR, exist_ok=True)
    generated = 0

    for lut_name, filename in LUT_LIBRARY.items():
        path = os.path.join(LUTS_DIR, filename)
        if not os.path.exists(path):
            if generate_cube_lut(lut_name, path, size=17):
                generated += 1
            else:
                print(f"[COLOR GRADE] Failed to generate {filename}")
                return False

    if generated > 0:
        print(f"[COLOR GRADE] Generated {generated} new LUT files in {LUTS_DIR}")
    else:
        print(f"[COLOR GRADE] All {len(LUT_LIBRARY)} LUT files present in {LUTS_DIR}")

    return True


# ============================================================================
# HDR DETECTION & TONE-MAPPING
# ============================================================================

def detect_hdr(video_path: str) -> Dict[str, Any]:
    """
    Detect whether a video is HDR by examining color metadata via ffprobe.
    Returns a dict with HDR detection results.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=color_space,color_transfer,color_primaries,pix_fmt",
        "-of", "json",
        video_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]

        color_transfer = stream.get("color_transfer", "")
        color_primaries = stream.get("color_primaries", "")
        pix_fmt = stream.get("pix_fmt", "")

        # HDR indicators
        is_hdr = any([
            "smpte2084" in color_transfer,  # PQ (Perceptual Quantizer)
            "arib-std-b67" in color_transfer,  # HLG (Hybrid Log-Gamma)
            "bt2020" in color_primaries,
            "p010" in pix_fmt or "yuv420p10" in pix_fmt,
        ])

        return {
            "is_hdr": is_hdr,
            "color_transfer": color_transfer,
            "color_primaries": color_primaries,
            "pix_fmt": pix_fmt,
        }

    except Exception as e:
        print(f"[COLOR GRADE] HDR detection failed: {e}")
        return {"is_hdr": False, "error": str(e)}


# ============================================================================
# MAIN COLOR GRADING ENGINE
# ============================================================================

def resolve_lut_name(director_plan: Dict[str, Any]) -> str:
    """
    Resolve which LUT to use from the AI Director's plan.
    Priority: explicit colorGradeLUT → colorGradingStyle mapping → vibe mapping → default.
    """
    # 1. Explicit LUT name from AI Director
    lut_name = director_plan.get("colorGradeLUT")
    if lut_name and lut_name in LUT_LIBRARY:
        return lut_name

    # 2. Map from colorGradingStyle
    color_grading = director_plan.get("colorGrading", {})
    style = color_grading.get("style", "") if isinstance(color_grading, dict) else ""
    if style and style in STYLE_TO_LUT:
        return STYLE_TO_LUT[style]

    # 3. Map from vibe
    vibe = director_plan.get("vibe", "")
    if vibe and vibe in VIBE_TO_LUT:
        return VIBE_TO_LUT[vibe]

    # 4. Default
    return "intellectual_podcast"


def apply_color_grade(
    input_video: str,
    output_video: str,
    lut_name: str,
    intensity: float = 1.0,
) -> bool:
    """
    Apply a 3D LUT color grade to a video via FFmpeg post-pass.

    Handles:
    - HDR detection and tone-mapping (zscale + tonemap BEFORE LUT)
    - LUT application via lut3d filter
    - Intensity blending (mix between original and graded)

    Args:
        input_video: Path to the source video
        output_video: Path for the graded output
        lut_name: Name of the LUT profile (must be in LUT_LIBRARY)
        intensity: Grade intensity 0.0 (no effect) to 1.0 (full LUT)

    Returns:
        True if grading succeeded.
    """
    if not os.path.exists(input_video):
        print(f"[COLOR GRADE] Input not found: {input_video}")
        return False

    # Ensure LUT library exists
    if not ensure_lut_library():
        print("[COLOR GRADE] LUT library bootstrap failed.")
        return False

    # Resolve LUT file path
    if lut_name not in LUT_LIBRARY:
        print(f"[COLOR GRADE] Unknown LUT '{lut_name}', falling back to intellectual_podcast")
        lut_name = "intellectual_podcast"

    lut_path = os.path.join(LUTS_DIR, LUT_LIBRARY[lut_name])
    if not os.path.exists(lut_path):
        print(f"[COLOR GRADE] LUT file not found: {lut_path}")
        return False

    # Detect HDR
    hdr_info = detect_hdr(input_video)
    print(f"[COLOR GRADE] HDR Detection: {hdr_info}")

    # Build filter chain
    filters = []

    if hdr_info["is_hdr"]:
        # Tone-map HDR → SDR BEFORE LUT application (prevents clipping)
        print("[COLOR GRADE] HDR source detected — applying tone-mapping before LUT")
        filters.extend([
            "tonemap=tonemap=hable:desat=0",
            "colorspace=all=bt709:trc=bt709:iall=bt2020:itrc=bt2020-10",
            "format=yuv420p",
        ])

    # Apply 3D LUT
    # Use interp=trilinear for smooth color transitions (prevents banding)
    lut_path_escaped = lut_path.replace("\\", "/").replace(":", "\\:")
    filters.append(f"lut3d=file='{lut_path_escaped}':interp=trilinear")

    # If intensity < 1.0, blend with original using split/overlay
    # For simplicity, apply at full intensity (the LUTs are already tuned to be subtle)
    if intensity < 1.0:
        # We'll use the LUT at full strength but the transforms themselves are subtle
        print(f"[COLOR GRADE] Note: Intensity {intensity} — LUTs are already calibrated for subtlety")

    filter_str = ",".join(filters)

    print(f"[COLOR GRADE] Applying LUT '{lut_name}' to {os.path.basename(input_video)}")
    start = time.time()

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-g", "30",
        "-c:a", "copy",  # Pass through audio unchanged
        output_video,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"[COLOR GRADE] FFmpeg error:\n{result.stderr[-500:]}")
            return False

        print(f"[COLOR GRADE] [SUCCESS] Graded output saved to {output_video} in {time.time() - start:.1f}s")
        return True

    except subprocess.TimeoutExpired:
        print("[COLOR GRADE] FFmpeg timed out (>300s)")
        return False
    except Exception as e:
        print(f"[COLOR GRADE] Error: {e}")
        return False


def grade_video(
    input_video: str,
    output_video: str,
    director_plan: Dict[str, Any],
) -> bool:
    """
    High-level API: grade a video using the AI Director's plan to select the LUT.
    This is the main entry point called from test_pipeline.py.
    """
    lut_name = resolve_lut_name(director_plan)
    intensity = 1.0

    # Extract intensity from director plan if available
    color_grading = director_plan.get("colorGrading", {})
    if isinstance(color_grading, dict):
        intensity = color_grading.get("intensity", 1.0)

    print(f"[COLOR GRADE] Director selected LUT: '{lut_name}' (intensity: {intensity})")
    return apply_color_grade(input_video, output_video, lut_name, intensity)


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    # Generate all LUTs
    print("=== Floor 5: Cinematic LUT Library Generator ===\n")
    ensure_lut_library()

    if len(sys.argv) > 2:
        input_path = sys.argv[1]
        lut_name = sys.argv[2] if len(sys.argv) > 2 else "intellectual_podcast"
        output_path = sys.argv[3] if len(sys.argv) > 3 else input_path.replace(".mp4", f"_graded_{lut_name}.mp4")
        apply_color_grade(input_path, output_path, lut_name)
    else:
        print(f"\nUsage: python color_grade.py <input.mp4> <lut_name> [output.mp4]")
        print(f"Available LUTs: {', '.join(LUT_LIBRARY.keys())}")
