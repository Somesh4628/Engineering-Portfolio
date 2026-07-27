"""Module docstring."""
import os

from gaitform.logging.db import DatasetLogger


def test_logger():
    db_path = "test_gaitform.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    logger = DatasetLogger(db_path)

    # 3 pipeline runs produce 3 fully-populated rows
    for i in range(3):
        logger.log_session(
            video_metadata={"filename": f"video_{i}.mp4"},
            raw_keypoints_path=f"data/keypoints_{i}.json",
            gait_metrics={"cadence": 120},
            orthotic_parameters={"arch": 15},
            stl_path=f"data/stl_{i}.stl",
            print_instructions_path=f"data/print_{i}.json",
        )

    sessions = logger.get_all_sessions()
    assert len(sessions) == 3

    sid = sessions[0]["session_id"]
    assert sessions[0]["clinician_outcome_notes"] is None

    # Attach outcome
    success = logger.attach_outcome(sid, "Patient felt improvement.")
    assert success

    sessions = logger.get_all_sessions()
    assert sessions[0]["clinician_outcome_notes"] == "Patient felt improvement."

    logger.export_to_csv("test_dataset.csv")
    assert os.path.exists("test_dataset.csv")

    os.remove(db_path)
    os.remove("test_dataset.csv")
