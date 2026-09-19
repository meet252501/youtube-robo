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

SOURCE_VIDEO = "raj_shamani.mp4"
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
    
    # 1. TRACKING & REFRAMING (Now with Punch-In enabled)
    print("\n--- 1. Testing Face Tracking & Reframing (With Audio Punch-In) ---")
    if not os.path.exists(CLIP_OUTPUT):
        print(f"Processing {SOURCE_VIDEO}...")
        start_time = time.time()
        # Using aspect ratio 9:16 (0.5625)
        # force_strategy="TRACK" forces the bounding-box face tracker (YOLOv8/Mediapipe)
        success = render(
            input_video=SOURCE_VIDEO,
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
            
    # Copy the reframed video to Remotion's public folder so it can access it
    os.makedirs("remotion/public", exist_ok=True)
    shutil.copy(CLIP_OUTPUT, "remotion/public/test_reframe_only.mp4")
    
    print("\n--- 3. Multimodal AI Creative Director: Visual Keyframe & Philosophical Transcript Analysis ---")
    from ai_director import analyze_transcript_and_direct
    director_plan = analyze_transcript_and_direct(transcript, video_path=CLIP_OUTPUT, video_title=SOURCE_VIDEO)
    
    props = {
        "videoUrl": "/test_reframe_only.mp4",
        "durationInFrames": int(frame_count),
        "fps": fps,
        "width": 1080,
        "height": 1920,
        "subtitles": {
            "captions": captions,
            "position": "bottom",
            "style": director_plan["subtitles"]
        },
        "hook": None, # Removed: No clashing header cards at start
        "focusBadge": None, # Removed: No top badges covering original disclaimers
        "effects": None,
        "progressBar": director_plan.get("progressBar"),
        "emojis": None, # Removed: No cartoon stickers
        "filmTexture": director_plan.get("filmTexture"),
        "audioVisualizer": None
    }
    
    from hook_variant_generator import generate_hook_variants
    print("\n--- 4. Multi-Hook Variant Generator (Floor 4) ---")
    hook_variants = generate_hook_variants(transcript, director_plan.get("vibe", "modern_podcast"))
    
    if not hook_variants:
        print("No hook variants generated. Falling back to single render.")
        hook_variants = [{"id": "default", "text": "", "type": "none"}]

    print(f"Generating {len(hook_variants)} variants for A/B Testing...")
    import subprocess
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    
    for i, variant in enumerate(hook_variants):
        variant_id = variant.get('id', f'var_{i}')
        hook_text = variant.get('text', '')
        
        print(f"\n>> Rendering Variant {i+1}: {variant_id.upper()}")
        print(f">> Hook Text: {hook_text}")
        
        # Inject the hook into props
        if hook_text:
            props["hook"] = {
                "text": hook_text,
                "size": "L",
                "position": "center",
                "style": "classic",
                "entranceAnimation": "spring",
                "displayDurationSec": 2.5
            }
        else:
            props["hook"] = None

        props_path = f"remotion/generated_props_{variant_id}.json"
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, indent=2)
            
        output_file = f"../output/test_final_remotion_{variant_id}.mp4"
        
        print(f"Running Remotion renderer for {variant_id} (universal YUV420P & 1s GOP)...")
        start_time = time.time()
        try:
            subprocess.run(
                [
                    npx_cmd, "remotion", "render",
                    "src/index.ts", "ShortVideo",
                    output_file,
                    f"--props=./generated_props_{variant_id}.json",
                    "--pixel-format=yuv420p",
                    "--codec=h264",
                    "--gop=30",
                    "--crf=18",
                    "--audio-codec=aac",
                    "--audio-bitrate=192k",
                    "--offthreadvideo-video-threads=4"
                ],
                cwd="remotion",
                check=True
            )
            print(f"Finished! Variant saved to {output_file} in {time.time() - start_time:.1f}s.")
        except Exception as e:
            print(f"Remotion render failed for variant {variant_id}: {e}")
            
    print("\n=== Running Auto-Comparison against Benchmark ===")
    subprocess.run([sys.executable, "compare_videos_nv.py"], check=False)

if __name__ == "__main__":
    main()
