import json
import pytest
from viral_detector import generate_candidates, pre_score_candidate, detect_viral_moments

def get_mock_words():
    return [
        {"word": "Well", "start": 0.0, "end": 0.5},
        {"word": "welcome", "start": 0.5, "end": 1.0},
        {"word": "back.", "start": 1.0, "end": 1.5},
        {"word": "It's", "start": 2.0, "end": 2.2},
        {"word": "easy", "start": 2.2, "end": 2.5},
        {"word": "to", "start": 2.5, "end": 2.7},
        {"word": "say", "start": 2.7, "end": 3.0},
        {"word": "simplify.", "start": 3.0, "end": 3.5},
        {"word": "It's", "start": 4.0, "end": 4.2},
        {"word": "very", "start": 4.2, "end": 4.5},
        {"word": "difficult", "start": 4.5, "end": 5.0},
        {"word": "to", "start": 5.0, "end": 5.2},
        {"word": "do", "start": 5.2, "end": 5.5},
        {"word": "it.", "start": 5.5, "end": 6.0},
        {"word": "I", "start": 6.5, "end": 6.7},
        {"word": "have", "start": 6.7, "end": 7.0},
        {"word": "this", "start": 7.0, "end": 7.2},
        {"word": "algorithm.", "start": 7.2, "end": 8.0},
        {"word": "Question", "start": 8.5, "end": 9.0},
        {"word": "requirements.", "start": 9.0, "end": 10.0},
        {"word": "Make", "start": 10.5, "end": 10.8},
        {"word": "them", "start": 10.8, "end": 11.0},
        {"word": "less", "start": 11.0, "end": 11.5},
        {"word": "dumb.", "start": 11.5, "end": 12.0},
        # Need to stretch it to 15s to be a valid candidate
        {"word": "Because", "start": 12.5, "end": 13.0},
        {"word": "they", "start": 13.0, "end": 13.2},
        {"word": "are", "start": 13.2, "end": 13.5},
        {"word": "always", "start": 13.5, "end": 14.0},
        {"word": "dumb.", "start": 14.0, "end": 15.0},
        {"word": "End", "start": 15.5, "end": 16.0},
        {"word": "of", "start": 16.0, "end": 16.5},
        {"word": "thought.", "start": 16.5, "end": 17.0},
    ]

def test_no_mid_sentence():
    words = get_mock_words()
    candidates = generate_candidates(words, min_duration_sec=10.0, max_duration_sec=30.0)
    
    for c in candidates:
        text = c["text"]
        # The last character of the candidate's text must be punctuation (or end of transcript)
        assert text[-1] in [".", "!", "?"] or text.endswith("thought")

def test_generic_interviewer_filler_penalty():
    words = get_mock_words()
    candidates = generate_candidates(words, min_duration_sec=10.0, max_duration_sec=30.0)
    
    c_start_filler = [c for c in candidates if c["text"].startswith("Well welcome back.")][0]
    score_filler = pre_score_candidate(c_start_filler)
    
    c_start_meat = [c for c in candidates if c["text"].startswith("It's easy to say simplify.")][0]
    score_meat = pre_score_candidate(c_start_meat)
    
    # Candidate starting with "Well welcome back" should be penalized heavily vs starting directly
    assert score_filler < score_meat

def test_fallback_works_when_llm_unavailable(monkeypatch):
    words = get_mock_words()
    # Force API key to be empty
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    clips = detect_viral_moments(words, top_k=2, min_score=40)
    
    assert len(clips) <= 2
    assert "whyItWorks" in clips[0]
    assert "heuristic" in clips[0]["whyItWorks"]
    
def test_top_k_ranking_stable(monkeypatch):
    words = get_mock_words()
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    clips1 = detect_viral_moments(words, top_k=3, min_score=0)
    clips2 = detect_viral_moments(words, top_k=3, min_score=0)
    
    # Deterministic fallback should be perfectly stable
    assert len(clips1) == len(clips2)
    assert clips1[0]["score"] == clips2[0]["score"]
