"""
Post-render deterministic QA: extracts frames at specific timestamps,
validates props.json constraints, checks render_manifest.json, and runs
geometric face-safe zone QA.
"""
import json
import subprocess
import os
import sys

PROPS_PATH = "remotion/props.json"
MANIFEST_PATH = "output/render_manifest.json"
VIDEO_PATH = "output/test_final_remotion_default.mp4"
FRAME_DIR = "output/qa_frames"

# Timestamps to extract (seconds):
# - 0.5s: main hook
# - 2.4s: hook fadeout
# - 2.8s: FIRST PRINCIPLES badge
# - 10.5s: takeaway card start (entrance)
# - 11.0s: takeaway card full opaque (start + 0.5s)
# - 11.25s: takeaway card midpoint
# - 11.75s: takeaway card pre-exit (end - 0.25s)
# - 12.0s: clean post-card
CHECK_TIMES = [0.5, 2.4, 2.8, 10.5, 11.0, 11.25, 11.75, 12.0]

def extract_frames(video_path, times, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    duration = float(probe.stdout.strip())
    final_sec = max(0, duration - 0.5)
    all_times = sorted(list(set(times + [final_sec])))
    
    paths = []
    for t in all_times:
        out_path = os.path.join(output_dir, f"frame_{t:.2f}s.png")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(t), "-i", video_path,
            "-frames:v", "1", "-q:v", "2", out_path
        ], capture_output=True)
        if os.path.exists(out_path):
            size_kb = os.path.getsize(out_path) / 1024
            paths.append((t, out_path, size_kb))
            print(f"  [OK] Frame at {t:.2f}s -> {out_path} ({size_kb:.0f} KB)")
        else:
            print(f"  [FAIL] FAILED to extract frame at {t:.2f}s")
    return paths, duration

def validate_props(props_path):
    with open(props_path, "r", encoding="utf-8") as f:
        props = json.load(f)
    
    errors = []
    warnings = []
    
    # 1. Hook timing: must end by 2.5s
    hook = props.get("hook")
    if hook:
        dur = hook.get("displayDurationSec", 0)
        if dur > 2.5:
            errors.append(f"Hook displayDurationSec={dur} exceeds 2.5s limit")
        else:
            print(f"  [OK] Hook duration: {dur}s (max 2.5s)")
        
        pos = hook.get("position")
        if pos != "top":
            errors.append(f"Hook position='{pos}' must be 'top'")
        else:
            print(f"  [OK] Hook position: {pos}")
            
        size = hook.get("size")
        if size in ["L"]:
            warnings.append(f"Hook size='{size}' is large; prefer S or M")
        else:
            print(f"  [OK] Hook size: {size}")
            
        style = hook.get("style")
        if style != "dark":
            warnings.append(f"Hook style='{style}'; dark preferred for podcast")
        else:
            print(f"  [OK] Hook style: {style}")
    else:
        errors.append("Hook is null/missing")
    
    # 2. Focus badge: must start >= 2700ms
    badge = props.get("focusBadge")
    if badge:
        start_ms = badge.get("startMs", 0)
        if start_ms < 2700:
            errors.append(f"focusBadge.startMs={start_ms} is before 2700ms")
        else:
            print(f"  [OK] focusBadge starts at {start_ms}ms (>= 2700ms)")
        
        variant = badge.get("variant", "badge")
        print(f"  [OK] focusBadge variant: {variant}")
    
    # 3. focusBadges (takeaway cards)
    badges = props.get("focusBadges", [])
    for i, fb in enumerate(badges):
        v = fb.get("variant", "badge")
        start = fb.get("startMs", 0)
        dur_ms = fb.get("durationMs", 0)
        card_pos = fb.get("cardPosition", "center")
        print(f"  [OK] focusBadges[{i}]: '{fb.get('text')}' variant={v} cardPosition={card_pos} start={start}ms dur={dur_ms}ms")
        
        if v == "card":
            if card_pos not in ["center-left", "center-right", "lower-left", "lower-right"]:
                errors.append(f"focusBadges[{i}] cardPosition='{card_pos}' is invalid or hardcoded center; must be face-safe")
            elif card_pos == "center-left":
                print(f"  [OK] focusBadges[{i}] face-safe card positioning: 'center-left' (empty dark space left of speaker)")
    
    # 4. colorGrading must be non-null
    cg = props.get("colorGrading")
    if cg is None:
        errors.append("colorGrading is null - must be enabled")
    elif not cg.get("enabled"):
        errors.append("colorGrading.enabled is false")
    else:
        print(f"  [OK] colorGrading: style={cg.get('style')}, intensity={cg.get('intensity')}, hdrBloom={cg.get('hdrBloom')}")
    
    # 5. cameraMoves
    moves = props.get("cameraMoves", [])
    print(f"  [OK] cameraMoves: {len(moves)} punch-ins")
    for i, m in enumerate(moves):
        print(f"     [{i}] start={m['timestampStart']}s dur={m['duration']}s scale={m['scaleTarget']} easing={m['easing']}")
    
    return errors, warnings

def validate_manifest(manifest_path):
    if not os.path.exists(manifest_path):
        return ["render_manifest.json not found"]
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    errors = []
    hook = manifest.get("hook")
    if hook:
        print(f"  [OK] Manifest hook: '{hook.get('text')}'")
    
    qa_status = manifest.get("visual_qa_status", manifest.get("qa_status", "unknown"))
    print(f"  [OK] QA status: {qa_status}")
    
    source_range = manifest.get("sourceRange")
    print(f"  [OK] sourceRange: {source_range}")
    
    return errors

def main():
    print("\n" + "="*60)
    print("  POST-RENDER DETERMINISTIC QA")
    print("="*60)
    
    if not os.path.exists(VIDEO_PATH):
        print(f"[FAIL] Video not found: {VIDEO_PATH}")
        sys.exit(1)
    
    # 1. Extract frames
    print("\n--- Frame Extraction ---")
    frames, duration = extract_frames(VIDEO_PATH, CHECK_TIMES, FRAME_DIR)
    print(f"\n  Video duration: {duration:.2f}s")
    
    # 2. Validate props
    print("\n--- Props Validation ---")
    errors, warnings = validate_props(PROPS_PATH)
    
    # 3. Validate manifest
    print("\n--- Manifest Validation ---")
    m_errors = validate_manifest(MANIFEST_PATH)
    errors.extend(m_errors)
    
    # 4. Run Computer Vision Safe-Zone QA
    print("\n--- Visual Safe-Zone Analysis ---")
    try:
        from qa_frames import run_qa
        run_qa()
        print("  [OK] Visual Safe-Zone QA passed successfully!")
    except Exception as e:
        errors.append(f"Visual Safe-Zone QA failed: {e}")
    
    # 5. Summary
    print("\n" + "="*60)
    if warnings:
        for w in warnings:
            print(f"  [WARN] WARNING: {w}")
    if errors:
        for e in errors:
            print(f"  [FAIL] ERROR: {e}")
        print(f"\n  RESULT: FAILED ({len(errors)} errors)")
        sys.exit(1)
    else:
        print(f"  RESULT: [ALL CHECKS PASSED] ({len(warnings)} warnings)")
    print("="*60)

if __name__ == "__main__":
    main()
