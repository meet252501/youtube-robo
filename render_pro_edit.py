import os
import sys
import json
import subprocess
import shutil

print("1. Preparing source...")
shutil.copy("output/test_capcut_color.mp4", "remotion/public/test_capcut_color.mp4")

# Load existing valid props that have startMs/endMs
with open("remotion/generated_props_body.json", "r", encoding="utf-8") as f:
    props = json.load(f)

# Update to use our newly colored video
props["videoUrl"] = "/test_capcut_color.mp4"

# Let's ensure the UI is visible and styled like a CapCut pro edit
if props.get("subtitles") and props["subtitles"].get("style"):
    props["subtitles"]["style"]["fontFamily"] = "Inter"
    props["subtitles"]["style"]["primaryTextColor"] = "#FFFFFF"
    props["subtitles"]["style"]["outlinePx"] = 4
    props["subtitles"]["style"]["highlightColor"] = "#FF3366" # Capcut style red/pink highlight
    props["subtitles"]["style"]["animation"] = "kinetic-slam"

os.makedirs("remotion", exist_ok=True)
with open("remotion/props.json", "w", encoding="utf-8") as f:
    json.dump(props, f, indent=2)

print("2. Rendering via Remotion...")
cmd = [
    "npx.cmd" if os.name == "nt" else "npx",
    "remotion", "render", "ShortVideo",
    "../output/pro_capcut_edit.mp4",
    "--props=props.json"
]
subprocess.run(cmd, cwd="remotion")
print("Done! View output/pro_capcut_edit.mp4")
