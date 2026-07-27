"""Module docstring."""
import cv2
import numpy as np


class NavicularTracker:
    def __init__(self, pixels_per_mm: float = 2.5):
        # Conversion factor (can be calibrated using a known reference like sticker diameter)
        self.pixels_per_mm = pixels_per_mm

        # HSV threshold for bright neon green sticker
        # Adjust these values based on actual lighting and sticker color
        self.lower_green = np.array([35, 100, 100])
        self.upper_green = np.array([85, 255, 255])

    def track_navicular_drop(self, video_path: str) -> dict:
        """
        Executes the 'One-Step Protocol' analysis.
        Finds the maximum height (baseline) and minimum height (dynamic load) of the sticker.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        max_y = None  # Highest point (lowest Y coordinate in pixels) -> Baseline
        min_y = None  # Lowest point (highest Y coordinate in pixels) -> Dynamic load

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Create a mask for neon green
            mask = cv2.inRange(hsv, self.lower_green, self.upper_green)

            # Find contours
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                # Get the largest contour assuming it's the sticker
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 50:
                    # Get center of the sticker
                    M = cv2.moments(largest_contour)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])

                        # In OpenCV, Y increases downwards.
                        # Baseline (highest physical point) has the MINIMUM Y pixel value
                        if max_y is None or cy < max_y:
                            max_y = cy

                        # Dynamic load (lowest physical point) has the MAXIMUM Y pixel value
                        if min_y is None or cy > min_y:
                            min_y = cy

        cap.release()

        if max_y is None or min_y is None:
            return {
                "success": False,
                "error": "Could not detect navicular sticker in video.",
                "drop_mm": 0.0,
            }

        # Calculate pixel drop
        drop_pixels = min_y - max_y  # Positive value

        # Convert to mm
        drop_mm = drop_pixels / self.pixels_per_mm

        return {
            "success": True,
            "drop_pixels": drop_pixels,
            "drop_mm": drop_mm,
            "baseline_y_px": max_y,
            "dynamic_y_px": min_y,
        }
