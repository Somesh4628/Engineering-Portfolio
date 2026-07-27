import cv2
import sys

def extract_frame(video_path, output_path, frame_ratio=0.5):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * frame_ratio))
    
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(output_path, frame)
        print(f"Saved {output_path}")
    else:
        print(f"Failed to read frame from {video_path}")
    cap.release()

extract_frame("20260705-1025-12.3859164.mp4", "extracted_vid1.png", 0.5)
extract_frame("gaitform.mp4", "extracted_vid2.png", 0.5)
