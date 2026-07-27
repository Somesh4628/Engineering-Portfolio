"""Module docstring."""
import csv
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class PressureMapResult:
    heel_peak_kpa: float
    midfoot_peak_kpa: float
    forefoot_peak_kpa: float
    total_frames: int
    source_file: str
    grid_data: np.ndarray


def parse_fscan_csv(filepath: str) -> Optional[PressureMapResult]:
    """
    Parses Tekscan F-Scan CSV export into zone-level peak pressures.
    Assumes a 60-row x 21-column sensor grid (standard F-Scan insole layout).
    Heel = rows 0-19, Midfoot = rows 20-39, Forefoot = rows 40-59.
    Returns None if file is unreadable or has wrong format.
    Clinical rationale: peak plantar pressure > 200kPa under heel or forefoot
    is associated with ulceration risk (Bus et al., Diabetes Metab Res Rev, 2016).
    """
    try:
        frames = []
        with open(filepath, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    values = [float(v) for v in row if v.strip()]
                    if len(values) == 60 * 21:
                        frames.append(np.array(values).reshape(60, 21))
                except ValueError:
                    continue
        if not frames:
            return None
        avg_map = np.mean(frames, axis=0)
        return PressureMapResult(
            heel_peak_kpa=float(np.max(avg_map[0:20, :])),
            midfoot_peak_kpa=float(np.max(avg_map[20:40, :])),
            forefoot_peak_kpa=float(np.max(avg_map[40:60, :])),
            total_frames=len(frames),
            source_file=filepath,
            grid_data=avg_map,
        )
    except Exception:
        return None
