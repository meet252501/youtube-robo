import os
import time
import subprocess
import json
import shutil
import cv2
import re
import hashlib
from datetime import datetime, timezone
from db_manager import (
    get_connection,
    update_project_status,
    add_clip,
    update_clip_status,
    create_render_task,
    get_pending_render_tasks,
    update_render_task_status,
    add_qa_result,
    execute_read
)
from viral_detector import detect_viral_moments
from subtitles import transcribe_audio
from ai_director import analyze_transcript_and_direct
from silence_stripper import strip_silences
from reframe_v2 import render as render_reframe
from color_grade import apply_color_grade
from qa_frames import run_qa
from ffmpeg_utils import get_export_encode_args

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["WHISPER_MODEL"] = "small"

def process_pending_projects():
    projects = execute_read("SELECT * FROM projects WHERE status = 'pending'")
    for proj in projects:
        print(f"Processing project {proj['id']} for source {proj['source_video_path']}")
        update_project_status(proj['id'], 'processing')
        
        try:
            full_transcript = transcribe_audio(proj['source_video_path'])
            all_words = []
            for segment in full_transcript.get('segments', []):
                all_words.extend(segment.get('words', []))
                
            top_clips = detect_viral_moments(all_words, top_k=3, min_score=0)
            
            for clip in top_clips:
                add_clip(
                    project_id=proj['id'],
                    start_time=clip['startMs'] / 1000.0,
                    end_time=clip['endMs'] / 1000.0,
                    score=clip.get('score', 0),
                    metadata=clip
                )
            update_project_status(proj['id'], 'completed')
            print(f"Project {proj['id']} completed. Added {len(top_clips)} clips.")
        except Exception as e:
            print(f"Failed to process project {proj['id']}: {e}")
            update_project_status(proj['id'], 'failed')

def process_pending_clips():
    clips = execute_read("SELECT * FROM clips WHERE status = 'pending'")
    for clip in clips:
        print(f"Processing clip {clip['id']} for render properties...")
        
        try:
            proj = execute_read("SELECT * FROM projects WHERE id = ?", (clip['project_id'],))[0]
            metadata = json.loads(clip['metadata'])
            mock_transcript = {"segments": [{"words": metadata.get("words", [])}]}
            
            director_plan = analyze_transcript_and_direct(
                transcript=mock_transcript, 
                video_path=proj['source_video_path'], 
                video_title=proj['source_video_path']
            )
            
            create_render_task(clip_id=clip['id'], render_props=director_plan)
            print(f"Render task created for clip {clip['id']}.")
        except Exception as e:
            print(f"Failed to create render task for clip {clip['id']}: {e}")
            update_clip_status(clip['id'], 'failed')

def process_pending_render_tasks():
    tasks = get_pending_render_tasks()
    for task in tasks:
        print(f"Processing render task {task['id']}...")
        update_render_task_status(task['id'], 'rendering')
        
        try:
            clip = execute_read("SELECT * FROM clips WHERE id = ?", (task['clip_id'],))[0]
            proj = execute_read("SELECT * FROM projects WHERE id = ?", (clip['project_id'],))[0]
            
            os.makedirs("output", exist_ok=True)
            
            # 1. Trim
            trimmed_source = f"output/trim_{task['id']}.mp4"
            trim_cmd = [
                "ffmpeg", "-y", "-i", proj['source_video_path'],
                "-ss", str(clip['start_time']), "-to", str(clip['end_time']),
                "-vf", "hqdn3d=4.0:4.0:3.0:3.0",
                "-c:v", "libx264", "-preset", "slow", "-crf", "10", "-c:a", "aac", trimmed_source
            ]
            subprocess.run(trim_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            # 2. Silence Stripper
            compressed_video = f"output/compressed_{task['id']}.mp4"
            strip_silences(trimmed_source, compressed_video, speed_multiplier=1.10)
            
            # 3. Reframe
            reframed_video = f"output/reframe_{task['id']}.mp4"
            render_reframe(
                input_video=compressed_video,
                final_output_video=reframed_video,
                aspect_ratio=9/16,
                force_strategy="GENERAL"
            )
            
            # 4. Transcribe trimmed video
            transcript = transcribe_audio(reframed_video)
            cap = cv2.VideoCapture(reframed_video)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            captions = []
            max_end_time_ms = 0
            for segment in transcript.get('segments', []):
                for word in segment.get('words', []):
                    raw_text = word['word'].strip()
                    clean_text = raw_text.strip(".,?!\"'()[]{}")
                    if not clean_text: continue
                    end_ms = int(word['end'] * 1000)
                    if end_ms > max_end_time_ms: max_end_time_ms = end_ms
                    captions.append({
                        "text": raw_text,
                        "startMs": int(word['start'] * 1000),
                        "endMs": end_ms
                    })
            duration_ms = max_end_time_ms + 300
            if fps: frame_count = int((duration_ms / 1000.0) * fps)
            
            # 5. Color Grade
            graded_output = f"output/graded_{task['id']}.mp4"
            apply_color_grade(reframed_video, graded_output, "intellectual_podcast")
            
            os.makedirs("remotion/public", exist_ok=True)
            pub_video = f"remotion/public/video_{task['id']}.mp4"
            shutil.copy(graded_output, pub_video)
            
            director_plan = json.loads(task['render_props'])
            props = {
                "videoUrl": f"/video_{task['id']}.mp4",
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
                        "animation": "kinetic-slam",
                        "borderWidth": 8,
                        "borderColor": "#000000"
                    })
                },
                "hook": director_plan.get("hook"),
                "focusBadge": director_plan.get("focusBadge"),
                "focusBadges": director_plan.get("focusBadges", []),
                "effects": director_plan.get("effects", {"segments": []}),
                "progressBar": director_plan.get("progressBar"),
                "emojis": {"items": director_plan.get("emojis")} if director_plan.get("emojis") else None,
                "colorGrading": director_plan.get("colorGrading"),
                "cameraMoves": director_plan.get("cameraMoves") or [],
            }
            
            with open("remotion/props.json", "w", encoding="utf-8") as f:
                json.dump(props, f, indent=2)
                
            raw_remotion_file = f"output/raw_remotion_{task['id']}.mp4"
            cmd = [
                "npx.cmd" if os.name == "nt" else "npx",
                "remotion", "render", "ShortVideo",
                "../" + raw_remotion_file,
                "--props=props.json",
                "--concurrency=1",
                "--crf=12",
                "--jpeg-quality=100"
            ]
            subprocess.run(cmd, cwd="remotion", check=True)
            
            base_name = os.path.splitext(os.path.basename(proj['source_video_path']))[0]
            final_output = f"output/{base_name}_clip_{int(clip['start_time'])}s_to_{int(clip['end_time'])}s_{task['id'][:4]}.mp4"
            # Loudnorm
            pass1_cmd = ["ffmpeg", "-y", "-i", raw_remotion_file, "-af", "loudnorm=I=-14:TP=-1.0:LRA=7:print_format=json", "-f", "null", "-"]
            res = subprocess.run(pass1_cmd, capture_output=True, text=True)
            match = re.search(r'(\{.*?\})', res.stderr, re.DOTALL)
            if match:
                loudnorm_stats = json.loads(match.group(1))
                pass2_cmd = [
                    "ffmpeg", "-y", "-i", raw_remotion_file,
                    "-af", f"loudnorm=I=-14:TP=-1.0:LRA=7:measured_I={loudnorm_stats.get('input_i')}:measured_LRA={loudnorm_stats.get('input_lra')}:measured_TP={loudnorm_stats.get('input_tp')}:measured_thresh={loudnorm_stats.get('input_thresh')}:linear=true",
                    "-c:v", "libx264"
                ] + get_export_encode_args() + [
                    "-crf", "15", "-preset", "slow", "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
                    final_output
                ]
                subprocess.run(pass2_cmd, check=True)
            else:
                shutil.copy(raw_remotion_file, final_output)
                
            with open("remotion/props.json", "rb") as f:
                props_hash = hashlib.sha256(f.read()).hexdigest()
                
            with open("output/render_manifest.json", "w", encoding="utf-8") as f:
                json.dump({
                    "renderedAt": datetime.now(timezone.utc).isoformat(), 
                    "videoPath": final_output,
                    "videoDurationMs": duration_ms,
                    "propsPath": "remotion/props.json",
                    "propsSha256": props_hash,
                    "hook": director_plan.get("hook"),
                    "finalCaptionEndMs": max_end_time_ms,
                    "sourceRange": {"startMs": clip['start_time']*1000, "endMs": clip['end_time']*1000}
                }, f, indent=2)
                
            try:
                run_qa()
                add_qa_result(task['id'], "passed", {"details": "Visual QA passed."})
            except Exception as qa_e:
                print(f"QA Failed: {qa_e}")
                add_qa_result(task['id'], "failed", {"details": str(qa_e)})
            
            update_render_task_status(task['id'], 'completed', output_path=final_output)
            print(f"Render task {task['id']} completed. Output: {final_output}")
        except Exception as e:
            print(f"Failed to process render task {task['id']}: {e}")
            update_render_task_status(task['id'], 'failed', error_message=str(e))

def run_worker_loop(once=False):
    print("Starting Queue Worker...")
    while True:
        process_pending_projects()
        process_pending_clips()
        process_pending_render_tasks()
        if once: break
        print("Sleeping...")
        time.sleep(10)

if __name__ == "__main__":
    run_worker_loop(once=True)
