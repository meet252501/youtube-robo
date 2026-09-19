import os
import sys
import time
from google import genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    benchmark_path = "benchmarks/benchmark_00001.mp4"
    our_video_path = "output/test_final_remotion.mp4"
    
    if not os.path.exists(benchmark_path):
        print(f"Benchmark not found: {benchmark_path}")
        sys.exit(1)
    if not os.path.exists(our_video_path):
        print(f"Our video not found: {our_video_path}")
        sys.exit(1)
        
    print(f"Uploading {benchmark_path} (Benchmark) to Gemini...")
    bench_file = client.files.upload(file=benchmark_path)
    print(f"Uploading {our_video_path} (Our Output) to Gemini...")
    our_file = client.files.upload(file=our_video_path)
    
    while bench_file.state.name == "PROCESSING" or our_file.state.name == "PROCESSING":
        print('.', end='', flush=True)
        time.sleep(2)
        bench_file = client.files.get(name=bench_file.name)
        our_file = client.files.get(name=our_file.name)
        
    if bench_file.state.name == "FAILED" or our_file.state.name == "FAILED":
        print("\nFailed to process videos.")
        sys.exit(1)
        
    prompt = """
    You are an expert video editor and QA analyst. I have uploaded two vertical videos.
    Video 1 (first one) is the BENCHMARK: A highly viral, professionally edited YouTube Short.
    Video 2 (second one) is OUR OUTPUT: An AI-generated Short we created to try and mimic the benchmark.
    
    The user is extremely unhappy because they feel OUR OUTPUT does not match the BENCHMARK.
    
    Watch both videos VERY closely. I need you to strictly grade OUR OUTPUT against the BENCHMARK on a scale of 0 to 100 for each of the following 4 categories. Be BRUTALLY HONEST. If it looks like cheap AI, give it a 20/100. We want a bare minimum established here.
    
    Categories:
    1. **Font Style & Sizing**: Compare the font family, thickness, size, case (uppercase/lowercase), and text stroke/shadow. How closely does ours match?
    2. **Animation & Physics**: Compare the "pop" or "bounce" effect. Is ours too slow, too fast, or lacking the correct spring physics?
    3. **Placement & Layout**: Are the captions placed in the exact same region (e.g., middle vs bottom)? Is the chunking (words per line) matching the benchmark?
    4. **Pacing & Framing**: Does the camera framing and face tracking feel as dynamic and professional as the benchmark?
    
    Output Format:
    For each category, provide:
    - Score: [0-100]/100
    - Exact Actionable Fixes: Exactly what pixel/CSS/timing values we need to change in our React/Remotion code to match the benchmark.
    
    At the end, provide a TOTAL SCORE out of 100.
    """
    
    print(f"\nAnalyzing both videos...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[bench_file, our_file, prompt]
    )
    print("--- COMPARISON ANALYSIS ---")
    print(response.text)
    print("---------------------------\n")
    
    client.files.delete(name=bench_file.name)
    client.files.delete(name=our_file.name)

if __name__ == "__main__":
    main()
