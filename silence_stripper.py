import os
import subprocess
import re
import time

def get_duration(video_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return float(res.stdout.strip())

def detect_silences(video_path: str, noise_db: str = "-35dB", min_duration: float = 0.4) -> list:
    print(f"   [Silence Stripper] Detecting silences (threshold {noise_db}, >{min_duration}s)...")
    cmd = [
        "ffmpeg", "-i", video_path, 
        "-af", f"silencedetect=noise={noise_db}:d={min_duration}",
        "-f", "null", "-"
    ]
    
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    _, stderr = process.communicate()
    
    silences = []
    current_start = None
    
    for line in stderr.split('\n'):
        if "silence_start" in line:
            match = re.search(r"silence_start: (\d+\.?\d*)", line)
            if match:
                current_start = float(match.group(1))
        elif "silence_end" in line and current_start is not None:
            match = re.search(r"silence_end: (\d+\.?\d*)", line)
            if match:
                current_end = float(match.group(1))
                silences.append((current_start, current_end))
                current_start = None
                
    return silences

def build_jumpcut_cmd(video_path: str, output_path: str, silences: list, duration: float, padding: float = 0.1, speed: float = 1.1) -> list:
    chunks = []
    last_end = 0.0
    
    # 1. Calculate the non-silent chunks
    for s_start, s_end in silences:
        chunk_start = last_end
        chunk_end = s_start + padding
        
        # Keep chunk if it's longer than a fraction of a second
        if chunk_end - chunk_start > 0.1:
            chunks.append((chunk_start, chunk_end))
            
        last_end = s_end - padding
        
    if duration - last_end > 0.1:
        chunks.append((last_end, duration))
        
    print(f"   [Silence Stripper] Found {len(silences)} silences. Compressing into {len(chunks)} tight jumpcuts at {speed}x speed.")
        
    # 2. Build the filter complex
    filter_complex = ""
    for i, (start, end) in enumerate(chunks):
        # We trim, reset timestamps, and apply speed up if requested
        if speed != 1.0:
            filter_complex += f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,setpts=(1/{speed})*PTS[v{i}]; "
            filter_complex += f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,atempo={speed}[a{i}]; "
        else:
            filter_complex += f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]; "
            filter_complex += f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]; "
        
    # Concat all the pieces
    for i in range(len(chunks)):
        filter_complex += f"[v{i}][a{i}]"
        
    filter_complex += f"concat=n={len(chunks)}:v=1:a=1[outv][outa]"
    
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    return cmd

def strip_silences(input_path: str, output_path: str, speed_multiplier: float = 1.10, noise_db: str = "-35dB", min_silence_duration: float = 0.4, padding: float = 0.1) -> bool:
    """
    Analyzes a video for silence, cuts it out, and applies a speed multiplier for adaptive WPM compression.
    Returns True if successful.
    """
    try:
        start_time = time.time()
        duration = get_duration(input_path)
        silences = detect_silences(input_path, noise_db, min_silence_duration)
        
        if not silences and speed_multiplier == 1.0:
            print("   [Silence Stripper] No silences found and speed is 1.0x. Skipping jumpcut pass.")
            # Just copy it over if absolutely nothing needs changing
            import shutil
            shutil.copy(input_path, output_path)
            return True
            
        cmd = build_jumpcut_cmd(input_path, output_path, silences, duration, padding, speed=speed_multiplier)
        
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            print(f"   [Silence Stripper] FFmpeg failed with error:\n{process.stderr}")
            return False
            
        new_duration = get_duration(output_path)
        print(f"   [Silence Stripper] Finished in {time.time() - start_time:.1f}s. Duration shrunk from {duration:.1f}s to {new_duration:.1f}s!")
        return True
    except Exception as e:
        print(f"   [Silence Stripper] Error processing silences: {e}")
        return False

if __name__ == "__main__":
    # Test execution
    strip_silences("raj_shamani.mp4", "output/test_compressed.mp4", speed_multiplier=1.1)
