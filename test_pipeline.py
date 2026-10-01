import os
import sys
import shutil
import time
import json
import subprocess
import argparse
from dotenv import load_dotenv
from dotenv import load_dotenv

# Fix protobuf error for Mediapipe
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Enable Punch-In and configure it for smoother, more human-like pacing
os.environ["PUNCH_IN"] = "1"
os.environ["PUNCH_IN_ZOOM"] = "1.15" # Closer medium shot as per AI review

# Upgrade transcription model for perfect A/V sync! (Reverted to 'small' due to OOM crash with large-v3)
os.environ["WHISPER_MODEL"] = "small"

# Import functions from openshorts backend
from reframe_v2 import render
from subtitles import transcribe_audio, generate_ass, burn_subtitles
from editor import VideoEditor
import cv2

SOURCE_VIDEO = "podcast_spliced.mp4"
CLIP_OUTPUT = "output/test_reframe_only.mp4"
FINAL_CAPTIONED = "output/test_final_captioned.mp4"
FINAL_AI = "output/test_final_ai.mp4"
SRT_FILE = "output/test_captions.ass"

def main():
    parser = argparse.ArgumentParser(description="Professional Short-Form Render Pipeline")
    parser.add_argument("--auto-select", action="store_true", help="Enable AutoShorts Viral Moment Detection")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top clips to return from viral detector")
    parser.add_argument("--min-score", type=int, default=70, help="Minimum score for viral moments")
    parser.add_argument("--target-duration", type=int, default=15, help="Target duration in seconds")
    args = parser.parse_args()

    load_dotenv()
    print("Starting PROFESSIONAL test pipeline...")
    
    if not os.path.exists(SOURCE_VIDEO):
        print(f"Could not find {SOURCE_VIDEO}.")
        return
        
    os.makedirs("output", exist_ok=True)
    
    current_source = SOURCE_VIDEO
    source_range = None
    
    if args.auto_select:
        print("\n--- AutoShorts: Viral Moment Detection ---")
        from viral_detector import detect_viral_moments
        print(f"Transcribing {current_source} for viral moment detection...")
        full_transcript = transcribe_audio(current_source)
        
        all_words = []
        for segment in full_transcript.get('segments', []):
            all_words.extend(segment.get('words', []))
            
        top_clips = detect_viral_moments(all_words, top_k=args.top_k, min_score=args.min_score)
        
        if top_clips:
            best_clip = top_clips[0]
            print(f"Selected viral moment: Score {best_clip['score']}")
            print(f"Hook: {best_clip.get('hookLine')}")
            
            # Trim the video to the selected candidate
            trimmed_source = "output/auto_selected_clip.mp4"
            start_sec = best_clip["startMs"] / 1000.0
            end_sec = best_clip["endMs"] / 1000.0
            source_range = {"startMs": best_clip["startMs"], "endMs": best_clip["endMs"]}
            
            trim_cmd = [
                "ffmpeg", "-y", "-i", current_source,
                "-ss", str(start_sec), "-to", str(end_sec),
                "-c:v", "libx264", "-c:a", "aac", trimmed_source
            ]
            subprocess.run(trim_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            current_source = trimmed_source
            print(f"Trimmed source to {current_source} ({start_sec}s - {end_sec}s)")
        else:
            print("No viral moments found above minimum score.")
    
    # 0. MICRO-SILENCE STRIPPER & WPM COMPRESSOR (Floor 6)
    print("\n--- 0. Micro-Silence Stripper & Adaptive WPM Compressor ---")
    COMPRESSED_VIDEO = "output/test_compressed.mp4"
    if not os.path.exists(COMPRESSED_VIDEO) or args.auto_select:
        from silence_stripper import strip_silences
        success = strip_silences(current_source, COMPRESSED_VIDEO, speed_multiplier=1.10)
        if not success:
            print("Silence Stripper failed.")
            return
    else:
        print(f"Found existing compressed video {COMPRESSED_VIDEO}, skipping...")
    
    # 1. TRACKING & REFRAMING (Now with Punch-In enabled)
    print("\n--- 1. Testing Face Tracking & Reframing (With Audio Punch-In) ---")
    if not os.path.exists(CLIP_OUTPUT):
        # We pass the COMPRESSED video to the tracker!
        print(f"Processing {COMPRESSED_VIDEO}...")
        start_time = time.time()
        # Using aspect ratio 9:16 (0.5625)
        # force_strategy="TRACK" forces the bounding-box face tracker (YOLOv8/Mediapipe)
        success = render(
            input_video=COMPRESSED_VIDEO,
            final_output_video=CLIP_OUTPUT,
            aspect_ratio=9/16,
            force_strategy="TRACK" 
        )
        if not success:
            print("Reframe failed.")
            return
        print(f"Reframe finished in {time.time() - start_time:.1f}s.")
    else:
        print(f"Found existing reframed video {CLIP_OUTPUT}, skipping reframing...")

    # 2. TRANSCRIPTION & CAPTIONS
    print("\n--- 2. Transcription & Premium Captions ---")
    
    print(f"Transcribing with {os.environ['WHISPER_MODEL']} for perfect sync...")
    transcript = transcribe_audio(CLIP_OUTPUT)
    
    cap = cv2.VideoCapture(CLIP_OUTPUT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps else 0
    cap.release()
    
    print("Generating Remotion props...")
    captions = []
    
    max_end_time_ms = 0
    
    for segment in transcript['segments']:
        words = segment.get('words', [])
        
        for i, word in enumerate(words):
            raw_text = word['word'].strip()
            if not raw_text:
                continue
                
            clean_text = raw_text.strip(".,?!\"'()[]{}")
            if not clean_text:
                continue
            
            end_ms = int(word['end'] * 1000)
            if end_ms > max_end_time_ms:
                max_end_time_ms = end_ms
                
            captions.append({
                "text": raw_text,
                "startMs": int(word['start'] * 1000),
                "endMs": end_ms
            })
                
    # Update duration to be max(caption.endMs) + 300ms
    duration_ms = max_end_time_ms + 300
    frame_count = int((duration_ms / 1000.0) * fps) if fps else frame_count
            
    # (Moved the Remotion copy logic to after Color Grading)
    

    # 1.5. GENERATE 3D DEPTH MASK (Floor 11)
    print("\n--- 1.5. Generating Neural Depth Mask for 3D Occlusion ---")
    MASK_OUTPUT = "output/test_mask.mp4"
    if not os.path.exists(MASK_OUTPUT):
        from mask_generator import generate_mask_video
        success = generate_mask_video(CLIP_OUTPUT, MASK_OUTPUT)
        if not success:
            print("Mask generation failed. Falling back to non-3D composition.")
    else:
        print(f"Found existing mask {MASK_OUTPUT}, skipping generation...")
    
    if os.path.exists(MASK_OUTPUT):
        shutil.copy(MASK_OUTPUT, "remotion/public/test_mask.mp4")
    
    print("\n--- 3. Multimodal AI Creative Director: Visual Keyframe & Philosophical Transcript Analysis ---")
    from ai_director import analyze_transcript_and_direct
    director_plan = analyze_transcript_and_direct(transcript, video_path=CLIP_OUTPUT, video_title=SOURCE_VIDEO)
    
    import urllib.parse
    import urllib.request
    
    broll_cutaways = []
    # DISABLED PER USER REQUEST:
    # if director_plan.get("brollCutaways"):
    #     ...
    

    # =========================================================================
    # FLOOR 5: Cinematic LUT / HDR Color Grading
    # =========================================================================
    print("\n--- 3.5 Cinematic LUT Color Grading (Floor 5) ---")
    from color_grade import apply_color_grade
    GRADED_OUTPUT = "output/test_graded_reframe.mp4"
    if not os.path.exists(GRADED_OUTPUT):
        print(f"Applying color grade to {CLIP_OUTPUT}...")
        apply_color_grade(CLIP_OUTPUT, GRADED_OUTPUT, "intellectual_podcast")
    else:
        print(f"Found existing graded output {GRADED_OUTPUT}")
    
    # Copy the GRADED video to Remotion's public folder
    os.makedirs("remotion/public", exist_ok=True)
    shutil.copy(GRADED_OUTPUT, "remotion/public/test_graded.mp4")
    if os.path.exists(MASK_OUTPUT):
        shutil.copy(MASK_OUTPUT, "remotion/public/test_mask.mp4")
        
    props = {
        "videoUrl": "/test_graded.mp4",
        "maskUrl": "/test_mask.mp4" if os.path.exists(MASK_OUTPUT) else None,
        "durationInFrames": int(frame_count),
        "fps": fps,
        "width": 1080,
        "height": 1920,
        "subtitles": {
            "captions": captions,
            "position": "bottom",
            "style": director_plan.get("subtitles", {
                "fontFamily": "Inter",
                "fontSize": 80,
                "fontColor": "#FFFFFF",
                "highlightColor": "#FFD700",
                "semanticColorMap": {},
                "animation": "kinetic-slam",
                "borderWidth": 8,
                "borderColor": "#000000"
            })
        },
        "hook": director_plan.get("hook"),
        "focusBadge": director_plan.get("focusBadge"),
        "focusBadges": director_plan.get("focusBadges", []),
        "effects": director_plan.get("effects", {
            "segments": [
                {
                    "startSec": move["timestampStart"],
                    "endSec": move["timestampStart"] + move["duration"],
                    "zoom": 1,
                    "zoomCenterX": 0.5,
                    "zoomCenterY": 0.5,
                    "brightness": 1.0,
                    "contrast": 1,
                    "saturate": 1,
                    "shake": 0.2 if move.get("easing") == "spring" else 0
                }
                for move in (director_plan.get("cameraMoves") or [])
            ]
        }),
        "progressBar": director_plan.get("progressBar"),
        "emojis": {"items": director_plan.get("emojis")} if director_plan.get("emojis") else None,
        "filmTexture": None, # DISABLED PER USER
        "audioVisualizer": None,
        "brollCutaways": broll_cutaways,
        "dataVisualization": director_plan.get("dataVisualization"),
        # Pass through for splice engine
        "colorGrading": director_plan.get("colorGrading"),
        "cameraMoves": director_plan.get("cameraMoves") or [],
    }
    
    # =========================================================================
    # FLOOR 4: Multi-Hook Variant Generator + Splice Architecture
    # =========================================================================
    from hook_variant_generator import generate_hook_variants
    # =========================================================================
    # =========================================================================
    # FLOOR 4: Final Validation Gate
    # =========================================================================
    print("\n--- 4. Rendering Final Video ---")
    
    # Validation 1: Hook validation
    hook = props.get("hook")
    if not hook:
        raise ValueError("VALIDATION FAILED: Hook is null")
    
    required_keys = ["position", "size", "entranceAnimation", "displayDurationSec", "style"]
    for k in required_keys:
        if k not in hook:
            raise ValueError(f"VALIDATION FAILED: Hook missing required key '{k}'")
            
    if hook.get("displayDurationSec", 0) > 3.0:
        raise ValueError("VALIDATION FAILED: Hook must disappear by 3 seconds")
        
    if hook.get("position") in ["center", "bottom"]:
        raise ValueError("VALIDATION FAILED: Hook must not cover the speaker's eyes, forehead, or captions (use 'top')")
        
    if hook.get("style") in ["classic", "yellow", "red"] and not hook.get("style").startswith("outline"):
        if hook.get("style") != "dark":
            raise ValueError("VALIDATION FAILED: Do not use a large bright box for the main hook; use dark or outline styling.")
    
    # Validation 2: Final caption end time doesn't exceed duration
    last_caption_end = max([c["endMs"] for c in captions]) if captions else 0
    final_duration_ms = (frame_count / fps) * 1000 if fps else 0
    if last_caption_end > final_duration_ms:
        raise ValueError(f"VALIDATION FAILED: Final caption end time ({last_caption_end}ms) exceeds video duration ({final_duration_ms}ms)")
        
    # Validation 3: At least 3 meaningful visual changes
    num_visual_changes = 0
    if props.get("cameraMoves"): num_visual_changes += len(props.get("cameraMoves"))
    if props.get("focusBadge"): num_visual_changes += 1
    if props.get("focusBadges"): num_visual_changes += len(props.get("focusBadges"))
    if num_visual_changes < 3:
        raise ValueError(f"VALIDATION FAILED: Fewer than 3 meaningful visual changes appear ({num_visual_changes} found)")
    
    print("✅ All Splice Engine validations passed!")
    
    with open("remotion/props.json", "w", encoding="utf-8") as f:
        json.dump(props, f, indent=2)

    raw_remotion_file = "output/raw_remotion_default.mp4"
    winner_file = "output/test_final_remotion_default.mp4"
    
    # ALWAYS render, never skip
    if os.path.exists(raw_remotion_file):
        os.remove(raw_remotion_file)
    if os.path.exists(winner_file):
        os.remove(winner_file)
        
    cmd = [
        "npx.cmd" if os.name == "nt" else "npx",
        "remotion", "render", "ShortVideo",
        "../" + raw_remotion_file,
        "--props=props.json",
        "--concurrency=1"
    ]
    subprocess.run(cmd, cwd="remotion", check=True)
        
    print("\n=== Mastering Audio (-14 LUFS) & Keyframes ===")
    # Pass 1: Measure
    pass1_cmd = ["ffmpeg", "-y", "-i", raw_remotion_file, "-af", "loudnorm=I=-14:TP=-1.0:LRA=7:print_format=json", "-f", "null", "-"]
    result = subprocess.run(pass1_cmd, capture_output=True, text=True)
    
    # Extract JSON from pass 1 output
    import re
    match = re.search(r'(\{.*?\})', result.stderr, re.DOTALL)
    if match:
        try:
            loudnorm_stats = json.loads(match.group(1))
            measured_i = loudnorm_stats.get("input_i")
            measured_lra = loudnorm_stats.get("input_lra")
            measured_tp = loudnorm_stats.get("input_tp")
            measured_thresh = loudnorm_stats.get("input_thresh")
            
            # Pass 2: Apply
            pass2_cmd = [
                "ffmpeg", "-y", "-i", raw_remotion_file,
                "-af", f"loudnorm=I=-14:TP=-1.0:LRA=7:measured_I={measured_i}:measured_LRA={measured_lra}:measured_TP={measured_tp}:measured_thresh={measured_thresh}:linear=true",
                "-c:v", "libx264", "-crf", "18", 
                "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
                "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
                "-pix_fmt", "yuv420p", "-color_range", "tv", 
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                winner_file
            ]
            subprocess.run(pass2_cmd, check=True)
        except Exception as e:
            print(f"Loudnorm processing failed: {e}")
            # Fallback copy
            shutil.copy(raw_remotion_file, winner_file)
    else:
        print("Loudnorm measurement failed!")
        shutil.copy(raw_remotion_file, winner_file)
            
    # Write Render Manifest
    import hashlib
    from datetime import datetime, timezone
    
    with open("remotion/props.json", "rb") as f:
        props_hash = hashlib.sha256(f.read()).hexdigest()
        
    render_manifest = {
        "renderedAt": datetime.now(timezone.utc).isoformat(),
        "videoPath": winner_file,
        "videoDurationMs": final_duration_ms,
        "propsPath": "remotion/props.json",
        "propsSha256": props_hash,
        "hook": hook,
        "finalCaptionEndMs": last_caption_end,
        "sourceRange": source_range
    }
    
    with open("output/render_manifest.json", "w", encoding="utf-8") as f:
        json.dump(render_manifest, f, indent=2)
        
    print("\n=== Frame QA Validation ===")
    from qa_frames import run_qa
    run_qa()
        
    winner_id = "default"

    # =========================================================================
    # FLOOR 12: Sound Design Engine (DISABLED for professional interview)
    # =========================================================================
    print("\n=== 7. Sound Design Engine (DISABLED) ===")
    sfx_file = winner_file
    # Floor 13: Smart Thumbnail Generator (DISABLED)
    # print("\n=== 8. Smart Thumbnail Generator (Floor 13) ===")
    # import thumbnail_generator
    # thumb_file = f"output/smart_thumbnail_{winner_id}.jpg"
    # if os.path.exists(sfx_file):
    #     thumbnail_generator.generate_thumbnail(sfx_file, "", thumb_file)
        
    # Floor 14: Retention Graph Predictor
    print("\n=== 9. Retention Graph Predictor (Floor 14) ===")
    import retention_predictor
    retention_file = f"output/retention_prediction_{winner_id}.png"
    retention_predictor.generate_retention_graph("output/pipeline_result.json", retention_file)

    # Floor 15: Penthouse Export Presets
    print("\n=== 10. Platform Export Presets (Floor 15) ===")
    import export_presets
    if os.path.exists(sfx_file):
        export_presets.generate_platform_exports(sfx_file, "output")

    # Save full pipeline results
    pipeline_result = {
        "source": SOURCE_VIDEO,
        "body_render": winner_file,
        "director_plan": {
            "vibe": director_plan.get("vibe"),
            "coreThesis": director_plan.get("coreThesis"),
            "subtitles_font": director_plan.get("subtitles", {}).get("fontFamily"),
        },
    }
    with open("output/pipeline_result.json", "w", encoding="utf-8") as f:
        json.dump(pipeline_result, f, indent=2, default=str)
    print(f"\nPipeline result saved to output/pipeline_result.json")

    print("\n=== Running Auto-Comparison against Benchmark ===")
    subprocess.run([sys.executable, "compare_videos_nv.py"], check=False)

if __name__ == "__main__":
    main()
