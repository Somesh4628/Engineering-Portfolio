"""Module docstring."""
import datetime
import json
import sqlite3
import uuid
from typing import Any, Dict


class DatasetLogger:
    def __init__(self, db_path: str = "gaitform.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT,
                video_metadata TEXT,
                raw_keypoints_path TEXT,
                gait_metrics TEXT,
                orthotic_parameters TEXT,
                stl_path TEXT,
                print_instructions_path TEXT,
                clinician_outcome_notes TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_session(
        self,
        video_metadata: Dict[str, Any],
        raw_keypoints_path: str,
        gait_metrics: Dict[str, Any],
        orthotic_parameters: Dict[str, Any],
        stl_path: str,
        print_instructions_path: str,
    ) -> str:
        session_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions
            (session_id, created_at, video_metadata, raw_keypoints_path, gait_metrics,
             orthotic_parameters, stl_path, print_instructions_path, clinician_outcome_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                created_at,
                json.dumps(video_metadata),
                raw_keypoints_path,
                json.dumps(gait_metrics),
                json.dumps(orthotic_parameters),
                stl_path,
                print_instructions_path,
                None,
            ),
        )
        conn.commit()
        conn.close()
        return session_id

    def get_all_sessions(self) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def attach_outcome(self, session_id: str, notes: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE sessions SET clinician_outcome_notes = ? WHERE session_id = ?
        """,
            (notes, session_id),
        )
        conn.commit()
        conn.close()
        return True

    def export_to_csv(self, output_path: str):
        import csv

        sessions = self.get_all_sessions()
        if not sessions:
            return
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sessions[0].keys())
            writer.writeheader()
            writer.writerows(sessions)
