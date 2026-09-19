import cv2
import numpy as np
import os
import sys

def generate_saliency_video(input_video: str, output_video: str):
    """
    Generates a simulated Saccadic Heatmap over the video to visualize
    where the viewer's eyes are drawn (Saliency Map).
    """
    if not os.path.exists(input_video):
        print(f"[SALIENCY] Input video not found: {input_video}")
        return

    print(f"[SALIENCY] Generating eye-tracking heatmap for {input_video}...")
    
    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    # Initialize the Static Saliency Spectral Residual detector
    # Note: Requires opencv-contrib-python
    try:
        saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
    except AttributeError:
        print("[SALIENCY] cv2.saliency not available. Ensure opencv-contrib-python is installed.")
        cap.release()
        out.release()
        return

    frame_count = 0
    max_frames = int(fps * 3) # Only do first 3 seconds for speed
    
    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Compute saliency map
        (success, saliencyMap) = saliency.computeSaliency(frame)
        if success:
            # Scale to 0-255
            saliencyMap = (saliencyMap * 255).astype("uint8")
            
            # Apply a heatmap colormap (e.g., JET or HOT)
            heatmap = cv2.applyColorMap(saliencyMap, cv2.COLORMAP_JET)
            
            # Overlay heatmap on original frame with 50% opacity
            overlay = cv2.addWeighted(frame, 0.5, heatmap, 0.5, 0)
            
            out.write(overlay)
        else:
            out.write(frame)
            
        frame_count += 1
        
    cap.release()
    out.release()
    print(f"[SALIENCY] Heatmap saved to {output_video}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        generate_saliency_video(sys.argv[1], sys.argv[2])
    else:
        generate_saliency_video("output/test_final_remotion_contradiction.mp4", "output/heatmap_debug.mp4")
