import os
import subprocess
import time

from ffmpeg_utils import get_export_encode_args

def generate_platform_exports(video_path: str, output_dir: str = "output"):
    """
    Floor 15: Penthouse - Platform-Optimized Export Presets.
    Takes the final mixed video and generates platform-specific formats.
    """
    print(f"[EXPORT] Generating platform presets for {video_path}...")
    
    os.makedirs(output_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(video_path))[0]
    
    # Enforce strict 30-frame GOP and precise SDR color tags across all platforms
    base_cmd = ["-c:v", "libx264"] + get_export_encode_args()
    
    presets = {
        "tiktok": {
            # TikTok compression is decent, 8M is sufficient
            "cmd": base_cmd + ["-b:v", "8M", "-maxrate", "8M", "-bufsize", "16M", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k"],
            "ext": "_tiktok.mp4"
        },
        "youtube_shorts": {
            # YouTube Shorts allows high bitrates and has good transcoder
            "cmd": base_cmd + ["-b:v", "10M", "-maxrate", "10M", "-bufsize", "20M", "-c:a", "aac", "-b:a", "192k"],
            "ext": "_shorts.mp4"
        },
        "instagram_reels": {
            # Reels ingest compression is extremely aggressive. We provide the highest possible 
            # bitrate here (12 Mbps) to give Instagram's engine maximum headroom to avoid artifacts.
            "cmd": base_cmd + ["-profile:v", "high", "-level", "4.2", "-b:v", "12M", "-maxrate", "12M", "-bufsize", "24M", "-c:a", "aac", "-b:a", "256k"],
            "ext": "_reels.mp4"
        }
    }
    
    for platform, config in presets.items():
        out_file = os.path.join(output_dir, f"{basename}{config['ext']}")
        cmd = ["ffmpeg", "-y", "-i", video_path] + config["cmd"] + [out_file]
        
        start = time.time()
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[EXPORT] ✅ {platform.upper()} preset saved to {out_file} ({time.time()-start:.1f}s)")
        except subprocess.CalledProcessError as e:
            print(f"[EXPORT] ❌ Failed to export for {platform}: {e.stderr}")

if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "output/test_final_sfx.mp4"
    generate_platform_exports(video)
