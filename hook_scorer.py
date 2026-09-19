import os
import json
import cv2
from typing import Dict, Any, List
from PIL import Image
from google import genai
from google.genai import types

def extract_first_3_seconds(video_path: str) -> List[Image.Image]:
    """Extracts 3 frames from the first 3 seconds of the video."""
    if not os.path.exists(video_path):
        return []
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames_to_grab = [0, int(fps * 1), int(fps * 2)]
        
        frames = []
        for frame_idx in frames_to_grab:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv2.resize(rgb, (360, 640)))
                frames.append(pil_img)
        cap.release()
        return frames
    except Exception as e:
        print(f"[HOOK SCORER] Error extracting frames: {e}")
        return []

def score_hook(video_path: str, hook_text: str) -> Dict[str, Any]:
    """
    Scores the hook of a video using Gemini Multimodal.
    Analyzes the visual pattern interrupt and curiosity gap of the text.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    fallback_score = {
        "score": 75,
        "retentionProbability": "75%",
        "rationale": "Fallback score. Gemini API key not found or error occurred."
    }
    
    if not api_key:
        return fallback_score
        
    try:
        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
        
        frames = extract_first_3_seconds(video_path)
        if not frames:
            return fallback_score
            
        prompt = f"""
        You are an expert viral video retention analyst and hook scorer.
        
        We are A/B testing a Short-form video. You are provided with:
        1. 3 ACTUAL VIDEO FRAMES representing the first 3 seconds of the video.
        2. The Hook Text on screen: "{hook_text}"
        
        YOUR MISSION:
        Analyze the hook based on:
        1. Visual Pattern Interrupt: Does the visual composition (lighting, text placement, subject framing) immediately catch the eye?
        2. Curiosity Gap: Does the text create an intense desire to find out what happens next?
        
        Score the hook from 0 to 100, where 100 means mathematically guaranteed to go viral.
        
        OUTPUT FORMAT:
        You MUST return a raw JSON object (and ONLY a JSON object) matching exactly this structure:
        {{
            "score": 85,
            "retentionProbability": "85%",
            "rationale": "A 1-sentence explanation of why it scored this way."
        }}
        """
        
        contents = frames + [prompt]
        
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        raw_text = response.text
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json\n", "").replace("```", "").strip()
            
        result = json.loads(raw_text)
        return result
        
    except Exception as e:
        print(f"[HOOK SCORER] Gemini scoring failed: {e}")
        return fallback_score

if __name__ == "__main__":
    # Test
    score = score_hook("output/test_final_remotion_contradiction.mp4", "Common health advice is wrong.")
    print(json.dumps(score, indent=2))
