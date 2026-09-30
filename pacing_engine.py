import os
import json
import subprocess
from typing import List, Dict, Any

def get_ffmpeg_silences(video_path: str, threshold_db: int = -35, duration_sec: float = 0.5) -> List[Dict[str, float]]:
    """
    Use FFmpeg silencedetect to find silences in the audio.
    """
    cmd = [
        "ffmpeg", "-v", "info",
        "-i", video_path,
        "-af", f"silencedetect=noise={threshold_db}dB:d={duration_sec}",
        "-f", "null", "-"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stderr.split('\n')
        
        silences = []
        current_start = None
        
        for line in lines:
            if "silence_start:" in line:
                parts = line.split("silence_start:")
                if len(parts) > 1:
                    current_start = float(parts[1].strip())
            elif "silence_end:" in line and current_start is not None:
                parts = line.split("silence_end:")
                if len(parts) > 1:
                    # silence_end: 2.5 | silence_duration: 0.5
                    end_str = parts[1].split("|")[0].strip()
                    end = float(end_str)
                    silences.append({
                        "start": current_start,
                        "end": end,
                        "duration": end - current_start
                    })
                    current_start = None
                    
        return silences
    except Exception as e:
        print(f"[PACING ENGINE] FFmpeg silencedetect failed: {e}")
        return []

def get_whisper_pauses(transcript: List[Dict[str, Any]], min_pause_sec: float = 0.5) -> List[Dict[str, float]]:
    """
    Use Whisper word-level timestamps to find gaps between words.
    """
    pauses = []
    for i in range(len(transcript) - 1):
        current_word = transcript[i]
        next_word = transcript[i + 1]
        
        if "end" in current_word and "start" in next_word:
            gap = next_word["start"] - current_word["end"]
            if gap >= min_pause_sec:
                pauses.append({
                    "start": current_word["end"],
                    "end": next_word["start"],
                    "duration": gap,
                    "type": "whisper_gap"
                })
                
    return pauses

def analyze_pacing(video_path: str, transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the video and transcript to recommend pacing cuts.
    """
    print(f"[PACING ENGINE] Analyzing pacing for {os.path.basename(video_path)}...")
    
    ffmpeg_silences = get_ffmpeg_silences(video_path, threshold_db=-35, duration_sec=0.5)
    whisper_pauses = get_whisper_pauses(transcript, min_pause_sec=0.5)
    
    print(f"[PACING ENGINE] Found {len(ffmpeg_silences)} FFmpeg silences and {len(whisper_pauses)} Whisper word gaps.")
    
    # Simple consensus: if Whisper says there's a gap AND FFmpeg says there's silence, it's a safe cut.
    # For POC, we just return the Whisper gaps as they are directly tied to speech semantics.
    safe_cuts = []
    
    for w_pause in whisper_pauses:
        # Cross-reference with FFmpeg
        is_true_silence = False
        for f_silence in ffmpeg_silences:
            # Overlap check
            if f_silence["start"] <= w_pause["end"] and f_silence["end"] >= w_pause["start"]:
                is_true_silence = True
                break
                
        if is_true_silence:
            # We leave a small pad of 0.1s around the cut for naturalness
            pad = 0.1
            cut_start = w_pause["start"] + pad
            cut_end = w_pause["end"] - pad
            if cut_end - cut_start > 0.2: # Only cut if remaining silence is > 0.2s
                safe_cuts.append({
                    "start": cut_start,
                    "end": cut_end,
                    "duration": cut_end - cut_start,
                    "rationale": "Consensus silence detected"
                })
                
    print(f"[PACING ENGINE] Recommended {len(safe_cuts)} safe cuts.")
    
    return {
        "ffmpeg_silences": ffmpeg_silences,
        "whisper_pauses": whisper_pauses,
        "safe_cuts": safe_cuts
    }

if __name__ == "__main__":
    # Test script will run this
    pass
