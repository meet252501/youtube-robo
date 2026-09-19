import os
import cv2
import base64
import requests
import numpy as np
from dotenv import load_dotenv

import subprocess
import glob
from PIL import Image

def get_frames(video_path, max_frames=3, prefix="frame"):
    frames = []
    # Clean up old frames
    for f in glob.glob(f"/tmp/{prefix}_*.jpg"):
        os.remove(f)
        
    # Extract frames using ffmpeg
    # -vf "fps=1/2,scale=400:711" extracts a frame every 2 seconds and resizes it to 400x711
    cmd = [
        "ffmpeg", "-y", "-i", video_path, 
        "-vf", f"fps={max_frames}/10,scale=400:711", 
        "-vframes", str(max_frames), 
        f"/tmp/{prefix}_%03d.jpg"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Read frames back
    for f in sorted(glob.glob(f"/tmp/{prefix}_*.jpg")):
        img = cv2.imread(f)
        if img is not None:
            frames.append(img)
            
    return frames[:max_frames]

def get_stitched_base64_image(bench_frames, our_frames):
    print(f"Stitching {len(bench_frames)} bench frames and {len(our_frames)} our frames...")
    # Ensure both have same number of frames
    if not bench_frames or not our_frames:
        return None
        
    # Concatenate horizontally
    bench_row = np.hstack(bench_frames)
    our_row = np.hstack(our_frames)
    
    print(f"Bench row shape: {bench_row.shape}, Our row shape: {our_row.shape}")
    
    # Ensure both rows have same width
    if bench_row.shape[1] != our_row.shape[1]:
        return None
        
    # Concatenate vertically
    grid = np.vstack([bench_row, our_row])
    
    _, buffer = cv2.imencode('.jpg', grid, [cv2.IMWRITE_JPEG_QUALITY, 80])
    b64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"

def main():
    load_dotenv()
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("Missing NVIDIA_API_KEY")
        return
        
    bench_file = "benchmarks/benchmark_00003.mp4"
    our_file = "output/test_final_remotion.mp4"
    
    print("Extracting frames and stitching...")
    bench_frames = get_frames(bench_file, max_frames=3, prefix="bench")
    our_frames = get_frames(our_file, max_frames=3, prefix="our")
    
    grid_b64 = get_stitched_base64_image(bench_frames, our_frames)
    if not grid_b64:
        print("Failed to stitch images")
        return
    
    prompt = """
    You are an objective computer vision measurement system. Your job is to compare the TOP ROW (Benchmark Video) to the BOTTOM ROW (Our Output Video).
    DO NOT invent or assume flaws. Only report exactly what is visible in the pixels.
    If they look visually identical in layout and style, you must state that they are identical.
    
    Evaluate on a strictly objective 0-100 scale based on visual facts:
    1. Typography & Stroke: Are the font weights, colors, and border thicknesses visually matched?
    2. Animation Scale: Does the text in the bottom row scale up similarly to the top row?
    3. Placement: Is the text centered at the exact same vertical and horizontal coordinates in both rows?
    
    Provide a factual summary of pixel-level differences (if any), followed by a TOTAL SCORE out of 100. Do not hallucinate errors.
    """
    
    content = [{"type": "text", "text": prompt}]
    content.append({"type": "image_url", "image_url": {"url": grid_b64}})
        
    print(f"\nAnalyzing both videos with NVIDIA meta/llama-3.2-11b-vision-instruct...")
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "meta/llama-3.2-11b-vision-instruct",
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 1024
        }
        response = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print("--- COMPARISON ANALYSIS ---")
        print(data["choices"][0]["message"]["content"])
        print("---------------------------")
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

if __name__ == "__main__":
    main()
