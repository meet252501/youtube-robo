import os
import json
import re
import math
from google import genai
from typing import List, Dict, Any, Optional

def _is_sentence_end(word: str) -> bool:
    return bool(re.search(r'[.!?]$', word.strip()))

def _is_filler(word: str) -> bool:
    w = word.lower().strip(".,!?")
    return w in ["um", "uh", "you know", "like", "so", "well", "right", "mean", "actually"]

def generate_candidates(transcript_words: List[Dict[str, Any]], min_duration_sec: float = 12.0, max_duration_sec: float = 35.0) -> List[Dict[str, Any]]:
    """
    Groups words into sentences, then creates sliding windows of 12-35s.
    """
    if not transcript_words:
        return []
        
    sentences = []
    current_sentence = []
    
    # Sentence tokenization based on punctuation and pauses
    for i, w in enumerate(transcript_words):
        current_sentence.append(w)
        
        is_end = _is_sentence_end(w["word"])
        
        # Check for pause > 1.5s as implicit sentence boundary
        pause = 0
        if i + 1 < len(transcript_words):
            pause = transcript_words[i+1]["start"] - w["end"]
            
        if is_end or pause > 1.5:
            if current_sentence:
                start_time = current_sentence[0]["start"]
                end_time = current_sentence[-1]["end"]
                text = " ".join([word["word"] for word in current_sentence])
                sentences.append({
                    "startMs": start_time * 1000,
                    "endMs": end_time * 1000,
                    "text": text,
                    "words": current_sentence
                })
                current_sentence = []
                
    if current_sentence:
        sentences.append({
            "startMs": current_sentence[0]["start"] * 1000,
            "endMs": current_sentence[-1]["end"] * 1000,
            "text": " ".join([w["word"] for w in current_sentence]),
            "words": current_sentence
        })

    candidates = []
    # Sliding window over sentences
    for i in range(len(sentences)):
        for j in range(i, len(sentences)):
            duration_sec = (sentences[j]["endMs"] - sentences[i]["startMs"]) / 1000.0
            
            if duration_sec > max_duration_sec:
                break
                
            if duration_sec >= min_duration_sec:
                cand_words = []
                for s in sentences[i:j+1]:
                    cand_words.extend(s["words"])
                    
                cand_text = " ".join([s["text"] for s in sentences[i:j+1]])
                candidates.append({
                    "startMs": sentences[i]["startMs"],
                    "endMs": sentences[j]["endMs"],
                    "durationSec": duration_sec,
                    "text": cand_text,
                    "words": cand_words,
                    "pre_score": 0
                })
                
    return candidates

def pre_score_candidate(candidate: Dict[str, Any]) -> float:
    """
    Deterministic scoring 0-100 based on heuristics.
    """
    score = 50.0
    words = candidate["words"]
    if not words:
        return 0
        
    text = candidate["text"]
    text_lower = text.lower()
    
    # Penalty: Starts with filler or generic setup
    first_few_words = [w["word"].lower().strip(".,!?") for w in words[:4]]
    if any(fw in ["um", "uh", "well", "welcome", "today", "joining"] for fw in first_few_words):
        score -= 20
        
    if "can you speak to" in text_lower or "tell us about" in text_lower:
        score -= 15
        
    # Bonus: Strong first 2 seconds (question, contradiction, bold claim)
    first_two_sec = [w["word"] for w in words if w["end"] <= words[0]["start"] + 2.0]
    first_two_text = " ".join(first_two_sec).lower()
    if "?" in first_two_text or any(b in first_two_text for b in ["never", "always", "truth", "secret", "lie", "easy", "hard", "difficult"]):
        score += 15
        
    # Bonus: Specificity (numbers, capitals)
    capitalized_count = sum(1 for w in words if w["word"].strip(".,!?").istitle() and w != words[0])
    number_count = sum(1 for w in words if any(char.isdigit() for char in w["word"]))
    score += min(15, (capitalized_count * 2) + (number_count * 3))
    
    # Penalty: High filler density
    filler_count = sum(1 for w in words if _is_filler(w["word"]))
    filler_ratio = filler_count / len(words)
    if filler_ratio > 0.05:
        score -= (filler_ratio * 100)
        
    # Bonus: Emotional intensity/concrete actionability
    if any(k in text_lower for k in ["you must", "do this", "step", "first principles", "algorithm", "million", "success", "fail"]):
        score += 15
        
    return max(0.0, min(100.0, score))

def detect_viral_moments(transcript_words: List[Dict[str, Any]], top_k: int = 3, min_score: int = 70) -> List[Dict[str, Any]]:
    # 1. Candidate Generation
    candidates = generate_candidates(transcript_words)
    
    # 2. Pre-scoring
    for c in candidates:
        c["pre_score"] = pre_score_candidate(c)
        
    # Sort and take top 10 for LLM
    top_candidates = sorted(candidates, key=lambda x: x["pre_score"], reverse=True)[:10]
    top_candidates = [c for c in top_candidates if c["pre_score"] >= min_score * 0.5] # Lenient pre-filter
    
    if not top_candidates:
        return []
        
    # 3. LLM Editorial Scoring
    try:
        import google.api_core.exceptions
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No Gemini API key")
            
        client = genai.Client(api_key=api_key)
        
        candidates_json = [{"id": i, "text": c["text"], "durationSec": c["durationSec"], "preScore": c["pre_score"]} for i, c in enumerate(top_candidates)]
        
        prompt = f"""
You are an elite short-form video editor (like an editor for Hormozi or Ali Abdaal).
Review these {len(top_candidates)} transcript clips. 
Rank the top {top_k} clips that will have the highest retention on TikTok/Shorts.

CRITICAL GROUNDING RULE: You must NOT invent any text. You must use the exact source text.

Return a JSON array of exactly {top_k} objects, matching this schema:
[{{
  "clipId": "index_from_input",
  "rank": 1,
  "score": 0-100,
  "hookStrength": 0-100,
  "clarity": 0-100,
  "novelty": 0-100,
  "payoff": 0-100,
  "visualPotential": 0-100,
  "hookLine": "exact source-grounded opening line from the text",
  "title": "short viewer-facing title",
  "whyItWorks": "brief explanation",
  "risks": ["missing context", "weak ending", "sensitive claim"],
  "mustKeepLines": ["exact transcript phrases"],
  "mustCutLines": ["filler or redundant phrases"]
}}]

Candidates:
{json.dumps(candidates_json, indent=2)}
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        raw_text = response.text
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json\n", "").replace("```", "").strip()
            
        llm_results = json.loads(raw_text)
        
        final_clips = []
        for res in llm_results:
            c_idx = int(res["clipId"])
            if c_idx < 0 or c_idx >= len(top_candidates):
                continue
            orig = top_candidates[c_idx]
            if res.get("score", 0) >= min_score:
                res["startMs"] = orig["startMs"]
                res["endMs"] = orig["endMs"]
                res["sourceTranscript"] = orig["text"]
                res["words"] = orig["words"]
                final_clips.append(res)
                
        # Sort by rank
        final_clips = sorted(final_clips, key=lambda x: x.get("rank", 99))
        return final_clips
        
    except Exception as e:
        print(f"⚠️ LLM Viral Scoring failed: {e}. Falling back to deterministic pre-scores.")
        final_clips = []
        for i, c in enumerate(top_candidates[:top_k]):
            if c["pre_score"] >= min_score:
                final_clips.append({
                    "clipId": str(i),
                    "rank": i + 1,
                    "score": c["pre_score"],
                    "startMs": c["startMs"],
                    "endMs": c["endMs"],
                    "sourceTranscript": c["text"],
                    "words": c["words"],
                    "hookLine": c["text"].split(".")[0],
                    "title": "Auto-Selected Clip",
                    "whyItWorks": "Selected via deterministic pre-scoring heuristic due to API failure.",
                    "risks": [],
                    "mustKeepLines": [],
                    "mustCutLines": []
                })
        return final_clips
