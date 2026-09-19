import os
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class HookVariant(BaseModel):
    id: str = Field(description="Unique identifier for this variant, e.g., 'contradiction'")
    text: str = Field(description="The actual hook text to display on screen (keep it under 8 words if possible)")
    type: str = Field(description="The psychological angle used: 'The Contradiction', 'The Stakes', or 'The Direct Reveal'")
    predicted_retention_hint: str = Field(description="A one-sentence rationale explaining why this hook should retain the viewer based on the transcript context.")

class HookVariantsList(BaseModel):
    hookVariants: List[HookVariant]

def generate_hook_variants(transcript: Dict[str, Any], vibe: str) -> List[Dict[str, Any]]:
    """
    Generates 3 distinct hook variants based on the full transcript and the AI Director's vibe.
    Returns exactly 3 variants: The Contradiction, The Stakes, and The Direct Reveal.
    """
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[HOOK GENERATOR] No Gemini API key found, skipping intelligent hook generation.")
        return get_fallback_hooks()
        
    genai.configure(api_key=api_key)
    
    # Reconstruct the transcript text
    full_text = ""
    for segment in transcript.get('segments', []):
        full_text += segment.get('text', '') + " "
        
    if not full_text.strip():
        return get_fallback_hooks()
        
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""
    You are an expert viral short-form video producer. We are creating a video with the following vibe: "{vibe}".
    
    Below is the full transcript of the video clip. We need to create exactly 3 distinct opening hook variations for A/B testing.
    The hooks must be punchy, extremely engaging, and ideally under 8 words. They will be displayed as text on screen for the first 2-3 seconds.
    
    Provide EXACTLY 3 variants using these specific psychological angles:
    1. The Contradiction — "Everyone believes X. Here's why that's wrong."
    2. The Stakes — "This decision cost/made them [outcome]."
    3. The Direct Reveal — states the most surprising fact immediately, no tease.
    
    Here is the transcript:
    {full_text.strip()}
    
    Return the result strictly as a JSON object matching the requested schema.
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=HookVariantsList
            )
        )
        
        result_json = type('obj', (object,), {'json': lambda: response.text})()
        import json
        data = json.loads(result_json.json())
        return data.get('hookVariants', get_fallback_hooks())
        
    except Exception as e:
        print(f"[HOOK GENERATOR] Gemini generation failed: {e}")
        return get_fallback_hooks()

def get_fallback_hooks() -> List[Dict[str, Any]]:
    return [
        {
            "id": "contradiction",
            "text": "Everyone thinks X is true. It's not.",
            "type": "The Contradiction",
            "predicted_retention_hint": "Challenges common beliefs immediately."
        },
        {
            "id": "stakes",
            "text": "This cost them everything.",
            "type": "The Stakes",
            "predicted_retention_hint": "High stakes create immediate curiosity."
        },
        {
            "id": "reveal",
            "text": "Here is the undeniable truth.",
            "type": "The Direct Reveal",
            "predicted_retention_hint": "Directness feels confident and authoritative."
        }
    ]

if __name__ == "__main__":
    # Test execution
    dummy_transcript = {"segments": [{"text": "If you don't sleep 8 hours, your brain literally starts eating itself. So you need to sleep."}]}
    variants = generate_hook_variants(dummy_transcript, "science_podcast")
    print(variants)
