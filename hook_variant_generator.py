"""
Floor 4 — Multi-Hook Variant Generator (A/B Testing)

Generates 3 distinct opening-hook variants per source clip using
three psychological angles:
  1. The Contradiction — "Everyone believes X. Here's why that's wrong."
  2. The Stakes — "This decision cost/made them [outcome]."
  3. The Direct Reveal — states the most surprising fact immediately, no tease.

Uses the modern google.genai.Client API (same as ai_director.py).
"""

import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types


def generate_hook_variants(transcript: Dict[str, Any], vibe: str) -> List[Dict[str, Any]]:
    """
    Generates 3 distinct hook variants based on the full transcript and the
    AI Director's determined vibe.

    Each variant returns:
      - id: unique identifier (e.g. "contradiction")
      - text: the actual hook text (under 8 words)
      - type: psychological angle used
      - predicted_retention_hint: one-sentence rationale (NOT a hard score — scoring is Floor 8)

    Args:
        transcript: Whisper transcript dict with 'segments' key
        vibe: The AI Director's determined vibe string (e.g. "intellectual_podcast")

    Returns:
        List of 3 hook variant dicts, or fallback defaults if API unavailable.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[HOOK GENERATOR] No Gemini API key found, skipping intelligent hook generation.")
        return get_fallback_hooks()

    # Reconstruct the transcript text
    full_text = ""
    for segment in transcript.get("segments", []):
        full_text += segment.get("text", "") + " "

    if not full_text.strip():
        print("[HOOK GENERATOR] Empty transcript, using fallback hooks.")
        return get_fallback_hooks()

    try:
        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"

        prompt = f"""
You are an expert viral short-form video producer. We are creating a video with the following vibe: "{vibe}".

Below is the full transcript of the video clip. We need to create exactly 3 distinct opening hook variations for A/B testing.
The hooks must be punchy, extremely engaging, and ideally under 8 words. They will be displayed as text on screen for the first 2-3 seconds.

Provide EXACTLY 3 variants using these specific psychological angles:
1. The Contradiction — "Everyone believes X. Here's why that's wrong." — challenges a common belief head-on.
2. The Stakes — "This decision cost/made them [outcome]." — raises urgency or consequence.
3. The Direct Reveal — states the most surprising fact from the transcript immediately, no tease.

TRANSCRIPT:
{full_text.strip()}

Return a JSON object with this exact structure:
{{
    "hookVariants": [
        {{
            "id": "contradiction",
            "text": "Hook text here",
            "type": "The Contradiction",
            "predicted_retention_hint": "One sentence rationale explaining why this hook retains viewers."
        }},
        {{
            "id": "stakes",
            "text": "Hook text here",
            "type": "The Stakes",
            "predicted_retention_hint": "One sentence rationale."
        }},
        {{
            "id": "reveal",
            "text": "Hook text here",
            "type": "The Direct Reveal",
            "predicted_retention_hint": "One sentence rationale."
        }}
    ]
}}
"""

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )

        raw_text = response.text
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json\n", "").replace("```", "").strip()

        data = json.loads(raw_text)
        variants = data.get("hookVariants", [])

        if len(variants) < 3:
            print(f"[HOOK GENERATOR] Only got {len(variants)} variants, padding with fallbacks.")
            fallbacks = get_fallback_hooks()
            while len(variants) < 3:
                variants.append(fallbacks[len(variants)])

        # Ensure all required fields exist
        for v in variants:
            v.setdefault("id", v.get("type", "unknown").lower().replace(" ", "_"))
            v.setdefault("text", "")
            v.setdefault("type", "Unknown")
            v.setdefault("predicted_retention_hint", "")

        print(f"[HOOK GENERATOR] Generated {len(variants)} hook variants:")
        for v in variants:
            print(f"   [{v['id']}] \"{v['text']}\" ({v['type']})")

        return variants

    except Exception as e:
        print(f"[HOOK GENERATOR] Gemini generation failed: {e}")
        return get_fallback_hooks()


def get_fallback_hooks() -> List[Dict[str, Any]]:
    """Returns 3 generic hook variants when Gemini API is unavailable."""
    return [
        {
            "id": "contradiction",
            "text": "Everyone thinks X is true. It's not.",
            "type": "The Contradiction",
            "predicted_retention_hint": "Challenges common beliefs immediately, creating cognitive dissonance.",
        },
        {
            "id": "stakes",
            "text": "This cost them everything.",
            "type": "The Stakes",
            "predicted_retention_hint": "High stakes create immediate curiosity about the outcome.",
        },
        {
            "id": "reveal",
            "text": "Here is the undeniable truth.",
            "type": "The Direct Reveal",
            "predicted_retention_hint": "Directness feels confident and authoritative, demanding attention.",
        },
    ]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    dummy_transcript = {
        "segments": [
            {
                "text": "If you don't sleep 8 hours, your brain literally starts eating itself. So you need to sleep."
            }
        ]
    }
    variants = generate_hook_variants(dummy_transcript, "science_podcast")
    print(json.dumps(variants, indent=2))
