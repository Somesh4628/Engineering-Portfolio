import numpy as np
from scipy.signal import find_peaks, detrend
from typing import Dict, Any
from gaitform.extraction.base import KeypointSequence


class GaitMetricsEngine:
    def __init__(
        self,
        keypoints: KeypointSequence,
        assumed_height_m: float = 1.75,
        **kwargs
    ):
        """
        assumed_height_m is a known prototype-level placeholder. A future version needs either 
        a real height input or a calibration reference (e.g. a known-length marker in frame).
        All distance-based metrics (stride length, foot length) inherit this limitation.
        """
        self.keypoints = keypoints
        self.fps = keypoints.fps
        # Support legacy keyword for app.py without breaking
        self.assumed_height_m = kwargs.get("patient_height_m", assumed_height_m)

    def _estimate_foot_length_mm(self, pixels_to_meters: float) -> float:
        """
        Estimates foot length based on the distance between HEEL and FOOT_INDEX landmarks.
        Inherits the assumed-height scale limitation from calibration. It varies per 
        subject but is not a validated absolute measurement.
        """
        lengths = []
        for f in self.keypoints.frames:
            l_heel = f.landmarks.get("LEFT_HEEL")
            l_toe = f.landmarks.get("LEFT_FOOT_INDEX")
            if l_heel and l_toe and l_heel.visibility > 0.5 and l_toe.visibility > 0.5:
                dist = np.sqrt((l_heel.x - l_toe.x)**2 + (l_heel.y - l_toe.y)**2)
                lengths.append(dist)
                
            r_heel = f.landmarks.get("RIGHT_HEEL")
            r_toe = f.landmarks.get("RIGHT_FOOT_INDEX")
            if r_heel and r_toe and r_heel.visibility > 0.5 and r_toe.visibility > 0.5:
                dist = np.sqrt((r_heel.x - r_toe.x)**2 + (r_heel.y - r_toe.y)**2)
                lengths.append(dist)
                
        if not lengths:
            return 260.0  # explicit fallback
            
        avg_len_meters = np.mean(lengths) * pixels_to_meters
        return float(avg_len_meters * 1000.0)

    def analyze(self) -> Dict[str, Any]:
        frames = self.keypoints.frames
        if not frames:
            return self._empty_metrics()

        # Extract vertical (y) trajectories for heels to find heel strikes
        # MediaPipe y is normalized [0, 1] with 0 at top, 1 at bottom.
        left_heel_y = []
        right_heel_y = []

        # also x for step width
        left_heel_x = []
        right_heel_x = []

        for f in frames:
            # Safely get y, default to 0 if not present
            l_heel = f.landmarks.get("LEFT_HEEL")
            r_heel = f.landmarks.get("RIGHT_HEEL")

            left_heel_y.append(l_heel.y if l_heel else 0.0)
            right_heel_y.append(r_heel.y if r_heel else 0.0)

            left_heel_x.append(l_heel.x if l_heel else 0.0)
            right_heel_x.append(r_heel.x if r_heel else 0.0)

        l_y_arr = np.array(left_heel_y)
        r_y_arr = np.array(right_heel_y)

        # Heel strike is when heel y is maximum (lowest on screen)
        # We detrend the signal to remove the perspective scaling as the person
        # walks towards the camera.
        detrended_l_y = detrend(l_y_arr) if len(l_y_arr) > 0 else l_y_arr
        detrended_r_y = detrend(r_y_arr) if len(r_y_arr) > 0 else r_y_arr

        l_peaks, _ = find_peaks(
            detrended_l_y, distance=int(self.fps * 0.5), prominence=0.01
        )
        r_peaks, _ = find_peaks(
            detrended_r_y, distance=int(self.fps * 0.5), prominence=0.01
        )

        total_steps = len(l_peaks) + len(r_peaks)
        duration_mins = len(frames) / self.fps / 60.0
        cadence = (total_steps / duration_mins) if duration_mins > 0 else 0.0

        # --- Deterministic Geometric Mappings ---

        # 1. Calibration
        # Assume height is self.patient_height_m meters. Calculate pixel-to-meter
        # scale from first frame.
        pixels_to_meters = 1.0  # fallback
        if len(frames) > 0:
            first_frame = frames[0]
            nose = first_frame.landmarks.get("NOSE")
            l_heel_first = first_frame.landmarks.get("LEFT_HEEL")
            r_heel_first = first_frame.landmarks.get("RIGHT_HEEL")
            if nose and (l_heel_first or r_heel_first):
                heels_y_first = []
                if l_heel_first:
                    heels_y_first.append(l_heel_first.y)
                if r_heel_first:
                    heels_y_first.append(r_heel_first.y)
                avg_heel_y = np.mean(heels_y_first)
                height_in_normalized = float(abs(avg_heel_y - nose.y))
                if height_in_normalized > 0.1:
                    pixels_to_meters = float(
                        self.assumed_height_m / height_in_normalized)

        # 2. Stride length (Deterministic depth estimation based on Y delta)
        def estimate_stride_length(peaks, heel_y_array):
            if len(peaks) < 2:
                return 0.75  # fallback
            diffs = [
                abs(heel_y_array[peaks[i]] - heel_y_array[peaks[i - 1]])
                for i in range(1, len(peaks))
            ]
            # empirically tuned, not yet formally validated against ground truth —
            # flagged for clinician calibration.
            return float(np.mean(diffs) * pixels_to_meters * 5.0)

        stride_length_L = estimate_stride_length(l_peaks, l_y_arr)
        stride_length_R = estimate_stride_length(r_peaks, r_y_arr)

        # 3. Step width (Temporal Alignment)
        step_widths = []
        for p_l in l_peaks:
            if len(r_peaks) > 0:
                closest_r = r_peaks[np.argmin(np.abs(r_peaks - p_l))]
                dist_x = abs(left_heel_x[p_l] - right_heel_x[closest_r])
                step_widths.append(dist_x * pixels_to_meters * 0.5)
        for p_r in r_peaks:
            if len(l_peaks) > 0:
                closest_l = l_peaks[np.argmin(np.abs(l_peaks - p_r))]
                dist_x = abs(left_heel_x[closest_l] - right_heel_x[p_r])
                step_widths.append(dist_x * pixels_to_meters * 0.5)

        step_width = float(np.mean(step_widths)) if step_widths else 0.05

        # 4. Stance / Swing %
        stance_time_pct = 60.0  # typical fixed assumption for frontal video
        swing_time_pct = 40.0

        # 5. Pronation angles (Deterministic angle of lower leg against vertical)
        def compute_pronation(knee_name, ankle_name):
            """
            Disclaimer: This calculates a 2D lean-angle proxy based on knee/ankle tracking.
            This is NOT true subtalar pronation. Used for prototype screening only.
            """
            angles = []
            for f in frames:
                knee = f.landmarks.get(knee_name)
                ankle = f.landmarks.get(ankle_name)
                if knee and ankle and knee.visibility > 0.5 and ankle.visibility > 0.5:
                    dx = ankle.x - knee.x
                    dy = ankle.y - knee.y
                    # angle with vertical (dy is down, dx is right/left)
                    angle = np.degrees(np.arctan2(abs(dx), dy))
                    angles.append(angle)
            return float(np.mean(angles)) if angles else 5.0

        pronation_angle_L_deg = compute_pronation("LEFT_KNEE", "LEFT_ANKLE")
        pronation_angle_R_deg = compute_pronation("RIGHT_KNEE", "RIGHT_ANKLE")

        # 5. LSI
        lsi = (
            min(stride_length_L, stride_length_R)
            / max(stride_length_L, stride_length_R)
            * 100
            if stride_length_R > 0
            else 100.0
        )

        foot_length_mm = self._estimate_foot_length_mm(pixels_to_meters)

        return {
            "cadence_steps_per_min": float(cadence),
            "stride_length_L_m": float(stride_length_L),
            "stride_length_R_m": float(stride_length_R),
            "step_width_m": float(step_width),
            "stance_time_pct": float(stance_time_pct),
            "swing_time_pct": float(swing_time_pct),
            "pronation_angle_L_deg": float(pronation_angle_L_deg),
            "pronation_angle_R_deg": float(pronation_angle_R_deg),
            "limb_symmetry_index": float(lsi),
            "foot_length_mm": float(foot_length_mm),
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            "cadence_steps_per_min": None,
            "stride_length_L_m": None,
            "stride_length_R_m": None,
            "step_width_m": None,
            "stance_time_pct": None,
            "swing_time_pct": None,
            "pronation_angle_L_deg": None,
            "pronation_angle_R_deg": None,
            "limb_symmetry_index": None,
            "foot_length_mm": None,
        }
