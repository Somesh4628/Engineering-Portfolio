import math
from gaitform.extraction.base import KeypointSequence, FrameKeypoints, Keypoint
from gaitform.metrics.analyzer import GaitMetricsEngine


def test_metrics_engine_cadence():
    # Create synthetic sine-wave keypoint data of known period
    fps = 30.0
    duration_secs = 4.0
    total_frames = int(fps * duration_secs)

    # 2 steps per second = 120 steps per minute
    # A step occurs at each peak.
    # Left heel sine wave: 1 Hz (1 peak per second)
    # Right heel sine wave: 1 Hz (1 peak per second), phase shifted by 180 degrees

    frames = []
    for i in range(total_frames):
        t = i / fps
        # max y is lowest on screen (heel strike)
        l_y = math.sin(2 * math.pi * 1.0 * t)
        r_y = math.sin(2 * math.pi * 1.0 * t + math.pi)

        frames.append(FrameKeypoints(
            frame_index=i,
            timestamp_ms=int(t * 1000),
            landmarks={
                "LEFT_HEEL": Keypoint(x=0.4, y=l_y, z=0.0, visibility=1.0),
                "RIGHT_HEEL": Keypoint(x=0.6, y=r_y, z=0.0, visibility=1.0)
            }
        ))

    seq = KeypointSequence(frames=frames, fps=fps)
    engine = GaitMetricsEngine(seq)
    metrics = engine.analyze()

    # Assert cadence is within 5% of 120
    assert "cadence_steps_per_min" in metrics
    cadence = metrics["cadence_steps_per_min"]
    assert 114 <= cadence <= 126
