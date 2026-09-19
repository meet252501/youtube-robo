import os
import sys
import time
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found.")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    
    benchmark_dir = "benchmarks"
    if not os.path.exists(benchmark_dir):
        print(f"Directory {benchmark_dir} not found.")
        sys.exit(1)
        
    videos = [os.path.join(benchmark_dir, f) for f in os.listdir(benchmark_dir) if f.endswith(".mp4")]
    if not videos:
        print("No benchmark videos found.")
        sys.exit(1)
        
    # Analyze the first 2 videos to save time/tokens
    videos_to_analyze = videos[:2]
    
    prompt = """
    You are an expert, professional video editor who specializes in high-retention YouTube Shorts (like Alex Hormozi or Raj Shamani styles).
    I have provided you with a highly successful, human-edited YouTube Short.
    
    Please analyze it in EXTREME detail. I need to replicate this EXACTLY in python using FFmpeg.
    Specifically tell me:
    1. Subtitles: Where are they positioned? (e.g. exactly middle, lower-third). What does the font look like? (Is it thick, sans-serif like Anton/Montserrat?). What colors are used? Are inactive words dimmed? Is there a black background box or just a stroke/drop-shadow?
    2. Pacing & Cuts: How often does the camera cut or zoom in? Does it zoom in on specific loud words?
    3. Visual Hooks: Are there emojis popping up? Are there B-roll images? Does the video flash or change color?
    
    Be as specific as possible with styling and pacing.
    """
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    for video_path in videos_to_analyze:
        print(f"Uploading {video_path} to Gemini...")
        video_file = genai.upload_file(path=video_path)
        
        while video_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            print(f"Failed to process {video_path}")
            continue
            
        print(f"\nAnalyzing {video_path}...")
        response = model.generate_content([video_file, prompt])
        print("--- ANALYSIS ---")
        print(response.text)
        print("----------------\n")
        
        genai.delete_file(video_file.name)

if __name__ == "__main__":
    main()
