import cv2
import numpy as np
from ultralytics import YOLO
import sys
import os

def generate_mask_video(input_video_path, output_video_path):
    """
    Reads an input video, runs YOLOv8 segmentation on each frame to extract the person,
    and writes a black & white mask video (person = white, background = black).
    """
    if not os.path.exists(input_video_path):
        print(f"Input video not found: {input_video_path}")
        return False
        
    print(f"Loading YOLOv8 segmentation model...")
    # 'yolov8n-seg.pt' is the nano version for speed.
    model = YOLO("yolov8n-seg.pt")
    
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Failed to open {input_video_path}")
        return False
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height), isColor=False)
    
    print(f"Generating mask video ({width}x{height}) at {fps} fps for {total_frames} frames...")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # We start with a fully black mask
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Run inference (classes=0 ensures we only detect 'person')
        results = model.predict(frame, classes=[0], verbose=False)
        
        if len(results) > 0 and results[0].masks is not None:
            # We take the largest person if there are multiple, or combine them
            masks_data = results[0].masks.data.cpu().numpy() # Shape: (N, H, W)
            # Resize the mask from the network size back to original frame size
            for i in range(masks_data.shape[0]):
                m = cv2.resize(masks_data[i], (width, height), interpolation=cv2.INTER_NEAREST)
                mask[m > 0.5] = 255
        
        out.write(mask)
        
        if frame_count % 30 == 0:
            print(f"Segmented {frame_count}/{total_frames} frames...")
            
    cap.release()
    out.write(mask) # just to be safe
    out.release()
    print(f"Mask generation complete: {output_video_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mask_generator.py <input.mp4> <output_mask.mp4>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    generate_mask_video(input_path, output_path)
