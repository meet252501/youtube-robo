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
    
    video_path = "output/test_final_captioned.mp4"
    if not os.path.exists(video_path):
        print(f"File {video_path} not found.")
        sys.exit(1)
        
    prompt = """
    You are an expert video QA analyst. I generated this vertical (9:16) video from a podcast using an automated Python script.
    The user complained: "how bad it look st facing and syncing". This means they think:
    1. The face tracking / framing is bad (e.g. face is cut off, not centered, moving erratically).
    2. The audio/subtitle syncing is bad (e.g. subtitles appear before or after the words are spoken).

    Watch this video VERY closely. Tell me exactly what is wrong.
    - Does the camera randomly jump or zoom in at weird times? At what timestamps?
    - Is the speaker's face cut off at the edges? At what timestamps?
    - Do the captions lag behind the audio? By how much? Give me specific words that appear late.
    
    Be brutally honest. I need to fix the Python code that generated this.
    """
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    print(f"Uploading {video_path} to Gemini...")
    video_file = genai.upload_file(path=video_path)
    
    while video_file.state.name == "PROCESSING":
        print('.', end='', flush=True)
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
        
    if video_file.state.name == "FAILED":
        print(f"Failed to process {video_path}")
        sys.exit(1)
        
    print(f"\nAnalyzing {video_path}...")
    response = model.generate_content([video_file, prompt])
    print("--- ANALYSIS ---")
    print(response.text)
    print("----------------\n")
    
    genai.delete_file(video_file.name)

if __name__ == "__main__":
    main()
