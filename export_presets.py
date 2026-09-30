import os
import subprocess
import time

def generate_platform_exports(video_path: str, output_dir: str = "output"):
    """
    Floor 15: Penthouse - Platform-Optimized Export Presets.
    Takes the final mixed video and generates platform-specific formats.
    """
    print(f"[EXPORT] Generating platform presets for {video_path}...")
    
    basename = os.path.splitext(os.path.basename(video_path))[0]
    
    presets = {
        "tiktok": {
            # TikTok likes faststart and specifically optimized bitrates
            "cmd": ["-c:v", "libx264", "-b:v", "8M", "-maxrate", "8M", "-bufsize", "16M", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k"],
            "ext": "_tiktok.mp4"
        },
        "youtube_shorts": {
            # Shorts allows higher bitrate but strictly prefers 4:2:0 YUV
            "cmd": ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"],
            "ext": "_shorts.mp4"
        },
        "instagram_reels": {
            # Reels strictly requires H.264 High Profile and AAC
            "cmd": ["-c:v", "libx264", "-profile:v", "high", "-level", "4.2", "-crf", "21", "-c:a", "aac", "-b:a", "256k"],
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
