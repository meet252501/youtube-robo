import os
import sys
import shutil
import time
import json
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

SOURCE_VIDEO = "podcast.mp4"
CLIP_OUTPUT = "output/test_reframe_only.mp4"
FINAL_CAPTIONED = "output/test_final_captioned.mp4"
FINAL_AI = "output/test_final_ai.mp4"
SRT_FILE = "output/test_captions.ass"

def main():
    load_dotenv()
    print("Starting PROFESSIONAL test pipeline...")
    
    if not os.path.exists(SOURCE_VIDEO):
        print(f"Could not find {SOURCE_VIDEO}.")
        return
        
    os.makedirs("output", exist_ok=True)
    
    # 0. MICRO-SILENCE STRIPPER & WPM COMPRESSOR (Floor 6)
    print("\n--- 0. Micro-Silence Stripper & Adaptive WPM Compressor ---")
    COMPRESSED_VIDEO = "output/test_compressed.mp4"
    if not os.path.exists(COMPRESSED_VIDEO):
        from silence_stripper import strip_silences
        success = strip_silences(SOURCE_VIDEO, COMPRESSED_VIDEO, speed_multiplier=1.10)
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
    for segment in transcript['segments']:
        for word in segment.get('words', []):
            raw_text = word['word'].strip()
            # Remove punctuation like OpusClip does for big impact captions
            clean_text = raw_text.strip(".,?!\"'()[]{}") 
            if clean_text:
                captions.append({
                    "text": clean_text,
                    "startMs": int(word['start'] * 1000),
                    "endMs": int(word['end'] * 1000)
                })
            
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
    # FLOOR 5: Cinematic LUT / HDR Color Grading (DISABLED PER USER)
    # =========================================================================
    print("\n--- 3.5 Cinematic LUT Color Grading (Floor 5) [DISABLED] ---")
    GRADED_OUTPUT = CLIP_OUTPUT # Bypass grading
    
    # Copy the UNGRADED video to Remotion's public folder
    os.makedirs("remotion/public", exist_ok=True)
    shutil.copy(GRADED_OUTPUT, "remotion/public/test_graded.mp4")
    
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
            "style": director_plan["subtitles"]
        },
        "hook": None, # Hook is now handled by the splice engine (Floor 4)
        "focusBadge": None, # Removed: No top badges covering original disclaimers
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
        "colorGrading": None,
        "cameraMoves": director_plan.get("cameraMoves") or [],
    }
    
    # =========================================================================
    # FLOOR 4: Multi-Hook Variant Generator + Splice Architecture
    # =========================================================================
    from hook_variant_generator import generate_hook_variants
    from splice_variants import run_splice_pipeline
    from hook_scorer import score_hook

    print("\n--- 4. Multi-Hook Variant Generator (Floor 4) ---")
    hook_variants = generate_hook_variants(transcript, director_plan.get("vibe", "modern_podcast"))
    
    if not hook_variants:
        print("No hook variants generated. Falling back to single body-only render.")
        hook_variants = [{"id": "default", "text": "", "type": "none"}]

    print(f"\n--- 4.1. Splice Architecture: 1 body + {len(hook_variants)} hook clips ---")
    hook_duration_sec = 2.5  # Each hook displays for 2.5 seconds

    splice_result = run_splice_pipeline(
        props=props,
        hook_variants=hook_variants,
        hook_duration_sec=hook_duration_sec,
        remotion_cwd="remotion",
        output_dir="output",
    )

    # =========================================================================
    # FLOOR 5 (FUTURE): Hook Scorer — score each variant
    # =========================================================================
    print("\n=== 5. Running AI Hook Scorer ===")
    scores_results = []
    for variant_info in splice_result.get("variants", []):
        variant_id = variant_info["variant_id"]
        output_file = variant_info["path"]
        if os.path.exists(output_file):
            print(f">> Scoring Variant: {variant_id}")
            score_data = score_hook(output_file, variant_info.get("hook_text", ""))
            score_data["variant_id"] = variant_id
            score_data["hook_type"] = variant_info.get("hook_type", "Unknown")
            scores_results.append(score_data)
            print(f"   Score: {score_data.get('score', 0)}/100")
            print(f"   Rationale: {score_data.get('rationale', '')}")
            
    if scores_results:
        # Sort by score descending
        scores_results = sorted(scores_results, key=lambda x: x.get("score", 0), reverse=True)
        with open("output/scores.json", "w", encoding="utf-8") as f:
            json.dump(scores_results, f, indent=2)
        winner_id = scores_results[0]['variant_id']
        print(f"\n🏆 WINNER: {winner_id} with {scores_results[0]['score']}/100!")
        
        # Generate Saliency Heatmap for the winner
        print("\n=== 6. Generating Saliency Heatmap for Winner ===")
        import saliency_heatmap
        winner_file = f"output/test_final_remotion_{winner_id}.mp4"
        heatmap_file = f"output/heatmap_winner_{winner_id}.mp4"
        if os.path.exists(winner_file):
            saliency_heatmap.generate_saliency_video(winner_file, heatmap_file)

        # Floor 12: Sound Design Engine
        print("\n=== 7. Sound Design Engine (Floor 12) ===")
        import sound_design
        sfx_file = f"output/test_final_sfx_{winner_id}.mp4"
        if os.path.exists(winner_file):
            sound_design.apply_sound_design(winner_file, sfx_file, director_plan)
            
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
        "body_render": splice_result.get("body_path"),
        "variants": splice_result.get("variants", []),
        "verification": splice_result.get("verification"),
        "scores": scores_results,
        "winner": scores_results[0] if scores_results else None,
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
    import subprocess
    subprocess.run([sys.executable, "compare_videos_nv.py"], check=False)

if __name__ == "__main__":
    main()
