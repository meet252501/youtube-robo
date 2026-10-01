import os
import json
import subprocess
from transcribe_backends import transcribe_media
from reframe_v2 import render
from color_grade import apply_color_grade
import shutil

SOURCE = "podcast.mp4"
REFRAMED = "output/podcast_reframed.mp4"
GRADED = "output/podcast_graded.mp4"
FINAL = "output/podcast_final.mp4"

os.makedirs("output", exist_ok=True)
os.makedirs("remotion/public", exist_ok=True)

# 1. Reframe without any cuts or edits
if not os.path.exists(REFRAMED):
    render(SOURCE, REFRAMED, 9/16, force_strategy="TRACK")

# 2. Color Grade
if not os.path.exists(GRADED):
    print("Color grading...")
    # Using CapCut style filters via color_grade.py
    apply_color_grade(REFRAMED, GRADED, "intellectual_podcast")

# 3. Transcribe
print("Transcribing...")
transcript = transcribe_media(GRADED)

# 4. Generate subtitles in Remotion format
captions = []
for segment in transcript.get("segments", []):
    for word in segment.get("words", []):
        captions.append({
            "text": word["word"].strip(),
            "startMs": int(word["start"] * 1000),
            "endMs": int(word["end"] * 1000)
        })

props = {
    "videoUrl": "/podcast_graded.mp4",
    "durationInFrames": int(45.0 * 30), # approx
    "fps": 30.0,
    "width": 1080,
    "height": 1920,
    "subtitles": {
        "captions": captions,
        "position": "bottom",
        "style": {
            "fontFamily": "Inter",
            "fontSize": 72,
            "primaryTextColor": "#FFFFFF",
            "highlightColor": "#FF3366",
            "animation": "kinetic-slam",
            "outlinePx": 4
        }
    },
    "hook": None,
    "focusBadge": None,
    "effects": {"segments": []},
    "progressBar": {"enabled": True, "position": "bottom", "color": "#FF3366"},
    "emojis": None
}

shutil.copy(GRADED, "remotion/public/podcast_graded.mp4")

with open("remotion/props.json", "w", encoding="utf-8") as f:
    json.dump(props, f, indent=2)

print("Rendering Remotion...")
cmd = [
    "npx.cmd" if os.name == "nt" else "npx",
    "remotion", "render", "ShortVideo",
    "../" + FINAL,
    "--props=props.json"
]
subprocess.run(cmd, cwd="remotion")
print(f"Done! Saved to {FINAL}")
