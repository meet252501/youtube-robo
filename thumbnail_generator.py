import os
import cv2
import json
import numpy as np

def generate_thumbnail(video_path: str, transcript_path: str, output_path: str):
    """
    Floor 13: Smart Thumbnail Generator.
    Extracts the highest saliency frame from the video and overlays text.
    For simplicity, we grab a frame at 1.5 seconds (during the hook)
    and use OpenCV to write bold thumbnail text.
    """
    print(f"[THUMBNAIL] Generating Smart Thumbnail for {video_path}...")
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30
    
    # Grab frame at 1.5 seconds (peak hook retention)
    target_frame = int(fps * 1.5)
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("[THUMBNAIL] Failed to read frame.")
        return False
        
    # Darken image slightly for text readability
    frame = cv2.convertScaleAbs(frame, alpha=0.7, beta=0)
    
    # Add vibrant text (Placeholder logic - in production we use PIL for custom fonts)
    text = "THE TRUTH!"
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 3
    thickness = 8
    color = (0, 255, 255) # Yellow in BGR
    
    # Get text size to center it
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = int(frame.shape[0] * 0.25) # Top 25%
    
    # Draw stroke
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, (0,0,0), thickness+4, cv2.LINE_AA)
    # Draw text
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)
    
    cv2.imwrite(output_path, frame)
    print(f"[THUMBNAIL] ✅ Thumbnail saved to {output_path}")
    return True

if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "output/test_final_remotion_contradiction.mp4"
    out = sys.argv[2] if len(sys.argv) > 2 else "output/smart_thumbnail.jpg"
    generate_thumbnail(video, "", out)
