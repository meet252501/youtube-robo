import os
import subprocess
import time

def apply_sound_design(video_path: str, output_path: str, director_plan: dict = None):
    """
    Floor 12: Sound Design Engine
    Auto-injects cinematic SFX (whooshes, bass hits, risers) via FFmpeg based on the AI director plan.
    Synchronizes bass hits with camera punch-ins/shakes, and whooshes with emojis/graphics.
    Uses FFmpeg synthetic generators to avoid needing external MP3s.
    """
    print(f"[SOUND_DESIGN] Applying cinematic sound design to {video_path}...")
    
    start = time.time()
    
    # Base command
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path
    ]
    
    filter_complex = []
    inputs = 1 # 0 is the original video
    mix_inputs = ["[0:a]"]
    
    # 1. Subtle ambient pad
    cmd.extend(["-f", "lavfi", "-i", "anoisesrc=c=pink:duration=15:a=0.03"])
    filter_complex.append(f"[{inputs}:a]afade=t=in:ss=0:d=1,afade=t=out:st=14:d=1[ambient];")
    mix_inputs.append("[ambient]")
    inputs += 1
    
    # Extract events
    bass_hits = []
    whooshes = []
    
    if director_plan:
        # Camera moves with spring get a bass hit impact
        camera_moves = director_plan.get("cameraMoves") or []
        for move in camera_moves:
            if move.get("easing") == "spring":
                bass_hits.append(move.get("timestampStart", 0.0))
                
        # Emojis and B-roll get a whoosh
        emojis = director_plan.get("emojis") or []
        for emoji in emojis:
            whooshes.append(emoji.get("startMs", 0.0) / 1000.0)
            
        brolls = director_plan.get("brollCutaways") or []
        for broll in brolls:
            whooshes.append(broll.get("timestampStart", 0.0))
            
    # Fallback for testing if no plan provided
    if not bass_hits and not whooshes:
        bass_hits.append(2.0)
        whooshes.append(5.0)
        
    # Generate bass hits
    for i, t in enumerate(bass_hits):
        cmd.extend(["-f", "lavfi", "-i", "sine=frequency=50:duration=1.0"])
        delay_ms = int(t * 1000)
        filter_complex.append(f"[{inputs}:a]afade=t=in:ss=0:d=0.05,afade=t=out:st=0.5:d=0.5,adelay={delay_ms}|{delay_ms},volume=0.8[bass{i}];")
        mix_inputs.append(f"[bass{i}]")
        inputs += 1
        
    # Generate whooshes (filtered white noise)
    for i, t in enumerate(whooshes):
        cmd.extend(["-f", "lavfi", "-i", "anoisesrc=c=white:duration=0.5:a=0.3"])
        delay_ms = int(t * 1000)
        # Bandpass filter sweeps down to create a whoosh
        filter_complex.append(f"[{inputs}:a]lowpass=f=2000,afade=t=in:ss=0:d=0.2,afade=t=out:st=0.2:d=0.3,adelay={delay_ms}|{delay_ms},volume=0.6[whoosh{i}];")
        mix_inputs.append(f"[whoosh{i}]")
        inputs += 1
        
    # Combine mix
    mix_str = "".join(mix_inputs)
    filter_complex.append(f"{mix_str}amix=inputs={inputs}:duration=first:dropout_transition=2[aout]")
    
    cmd.extend([
        "-filter_complex", "".join(filter_complex),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[SOUND_DESIGN] ✅ Sound design applied in {time.time() - start:.1f}s -> {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[SOUND_DESIGN] ❌ FFmpeg failed: {e.stderr}")
        return False

if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "output/test_final_remotion_contradiction.mp4"
    out = sys.argv[2] if len(sys.argv) > 2 else "output/test_final_sfx.mp4"
    apply_sound_design(video, out)
