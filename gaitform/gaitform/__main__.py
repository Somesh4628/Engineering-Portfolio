"""Module docstring."""
import argparse
import json
import os
from typing import Optional

from gaitform.cad.generator import CADGenerator
from gaitform.extraction import MediaPipeGaitExtractor
from gaitform.logging.db import DatasetLogger
from gaitform.mapping.rules import OrthoticParameterMapper, OrthoticParams, RigidityZone
from gaitform.metrics.analyzer import GaitMetricsEngine


def run_pipeline(
    video_path: str,
    height_m: float = 1.75,
    scan_left: Optional[str] = None,
    scan_right: Optional[str] = None,
    shoe_size_mm: float = 273.0,
    pressure_csv: Optional[str] = None,
    navicular_video_left: Optional[str] = None,
    navicular_video_right: Optional[str] = None,
):
    print(f"Running pipeline on {video_path} (Height: {height_m}m)")
    extractor = MediaPipeGaitExtractor()
    keypoints = extractor.extract(video_path)

    analyzer = GaitMetricsEngine(keypoints, patient_height_m=height_m)
    metrics = analyzer.analyze()

    from gaitform.extraction.navicular import NavicularTracker

    tracker = NavicularTracker()

    if navicular_video_left:
        nav_results_L = tracker.track_navicular_drop(navicular_video_left)
        if nav_results_L.get("success"):
            metrics["navicular_drop_L_mm"] = nav_results_L["drop_mm"]
            print(f"Left Navicular Drop Detected: {nav_results_L['drop_mm']:.2f}mm")
        else:
            metrics["navicular_drop_L_mm"] = 0.0
            print(f"Left Navicular Tracking Failed: {nav_results_L.get('error')}")
    else:
        metrics["navicular_drop_L_mm"] = 0.0
        print("No Left Navicular video provided.")

    if navicular_video_right:
        nav_results_R = tracker.track_navicular_drop(navicular_video_right)
        if nav_results_R.get("success"):
            metrics["navicular_drop_R_mm"] = nav_results_R["drop_mm"]
            print(f"Right Navicular Drop Detected: {nav_results_R['drop_mm']:.2f}mm")
        else:
            metrics["navicular_drop_R_mm"] = 0.0
            print(f"Right Navicular Tracking Failed: {nav_results_R.get('error')}")
    else:
        metrics["navicular_drop_R_mm"] = 0.0
        print("No Right Navicular video provided.")

    from gaitform.sensors.pressure_parser import parse_fscan_csv

    _default_csv = os.path.join(
        os.path.dirname(__file__), "..", "data", "demo_pressure.csv"
    )
    _csv_to_load = (
        pressure_csv
        if pressure_csv
        else (_default_csv if os.path.exists(_default_csv) else None)
    )
    pressure_data = parse_fscan_csv(_csv_to_load) if _csv_to_load else None

    mapper = OrthoticParameterMapper()
    params_dict = mapper.map_metrics_to_orthotic(metrics, pressure=pressure_data)

    import trimesh as _trimesh

    def _load_scan(path):
        """Load a scan STL from disk into a trimesh object, or return None."""
        if not path:
            return None
        try:
            mesh = _trimesh.load(path)
            if not isinstance(mesh, _trimesh.Trimesh):
                return None
            return mesh
        except Exception:
            return None

    # shoe_size_mm (user-confirmed physical size) drives the shell dimensions.
    # foot_length_mm (video-estimated anatomical length) drives met_pad_position
    # via the rules engine. These are intentionally separate.
    # If shoe_size_mm was not provided (default 273.0), fall back to pipeline estimate.
    shell_length = shoe_size_mm if shoe_size_mm != 273.0 else metrics.get("foot_length_mm", 273.0)
    generator = CADGenerator(length_mm=shell_length)
    mesh_left = generator.generate_mesh(
        params_dict["left"],
        scan_mesh=_load_scan(scan_left),
        foot_side="left",
    )
    mesh_right = generator.generate_mesh(
        params_dict["right"],
        scan_mesh=_load_scan(scan_right),
        foot_side="right",
    )

    mesh_left.export("orthotic_left.stl")
    mesh_right.export("orthotic_right.stl")

    generator.generate_zoning(
        params_dict["left"],
        "print_instructions_left.json",
        "heatmap_left.png",
        foot_side="left",
    )
    generator.generate_zoning(
        params_dict["right"],
        "print_instructions_right.json",
        "heatmap_right.png",
        foot_side="right",
    )

    print("Pipeline complete. Left and Right STL, JSON, and PNG files generated.")

    # Log this session to the dataset DB for outcome tracking and before/after comparison.
    try:
        import json as _json
        _logger = DatasetLogger()
        _params_serialisable = {
            side: {
                k: (v if not hasattr(v, '__iter__') or isinstance(v, str) else
                    [z.__dict__ if hasattr(z, '__dict__') else z for z in v])
                for k, v in params_dict[side].__dict__.items()
            }
            for side in ("left", "right")
        }
        _logger.log_session(
            video_metadata={"video_path": video_path, "height_m": height_m, "shoe_size_mm": shoe_size_mm},
            raw_keypoints_path="",
            gait_metrics=metrics,
            orthotic_parameters=_params_serialisable,
            stl_path="orthotic_left.stl,orthotic_right.stl",
            print_instructions_path="print_instructions_left.json,print_instructions_right.json",
        )
    except Exception as _log_err:
        print(f"Session logging failed (non-fatal): {_log_err}")

    return metrics


def map_parameters(video_path: str, output_path: str, height_m: float = 1.75):
    print(f"Mapping parameters for {video_path} (Height: {height_m}m)")
    extractor = MediaPipeGaitExtractor()
    keypoints = extractor.extract(video_path)

    analyzer = GaitMetricsEngine(keypoints, patient_height_m=height_m)
    metrics = analyzer.analyze()

    mapper = OrthoticParameterMapper()
    params_dict = mapper.map_metrics_to_orthotic(metrics)

    out_data = {
        "orthotic_parameters": {
            "left": params_dict["left"].to_dict(),
            "right": params_dict["right"].to_dict(),
        }
    }

    with open(output_path, "w") as f:
        json.dump(out_data, f, indent=2)

    print(f"Parameters mapped and saved to {output_path}")


def generate_cad(
    params_path, stl_base, json_base, png_base, scan_left=None, scan_right=None
):
    with open(params_path, "r") as f:
        data = json.load(f)

    left_data = data["orthotic_parameters"]["left"]
    right_data = data["orthotic_parameters"]["right"]

    # Reconstruct OrthoticParams objects
    def parse_params(d):
        return OrthoticParams(
            arch_height_mm=d["arch_height_mm"],
            heel_cup_depth_mm=d["heel_cup_depth_mm"],
            medial_post_deg=d["medial_post_deg"],
            lateral_post_deg=d["lateral_post_deg"],
            met_pad_position_mm=d["met_pad_position_mm"],
            rigidity_zones=[
                RigidityZone(**z) if isinstance(z, dict) else z
                for z in d["rigidity_zones"]
            ],
            flags_for_review=d.get("flags_for_review", []),
        )

    left_params = parse_params(left_data)
    right_params = parse_params(right_data)

    import trimesh as _trimesh

    def _load_scan(path):
        """Load a scan STL from disk into a trimesh object, or return None."""
        if not path:
            return None
        try:
            mesh = _trimesh.load(path)
            if not isinstance(mesh, _trimesh.Trimesh):
                return None
            return mesh
        except Exception:
            return None

    generator = CADGenerator()
    mesh_left = generator.generate_mesh(
        left_params, scan_mesh=_load_scan(scan_left), foot_side="left"
    )
    mesh_right = generator.generate_mesh(
        right_params, scan_mesh=_load_scan(scan_right), foot_side="right"
    )

    out_dir = os.path.dirname(stl_base)

    mesh_left.export(os.path.join(out_dir, "orthotic_left.stl"))
    mesh_right.export(os.path.join(out_dir, "orthotic_right.stl"))

    generator.generate_zoning(
        left_params,
        os.path.join(out_dir, "print_instructions_left.json"),
        os.path.join(out_dir, "heatmap_left.png"),
        foot_side="left",
    )
    generator.generate_zoning(
        right_params,
        os.path.join(out_dir, "print_instructions_right.json"),
        os.path.join(out_dir, "heatmap_right.png"),
        foot_side="right",
    )


def compare_sessions(before_id: str, after_id: str):
    import sqlite3

    from gaitform.logging.db import DatasetLogger

    logger = DatasetLogger()
    sessions = logger.get_all_sessions()

    before_session = next((s for s in sessions if s["session_id"] == before_id), None)
    after_session = next((s for s in sessions if s["session_id"] == after_id), None)

    if not before_session or not after_session:
        print("Error: One or both session IDs not found in database.")
        return

    before_metrics = json.loads(before_session["gait_metrics"])
    after_metrics = json.loads(after_session["gait_metrics"])

    # Clinical rationale:
    # Normal walking pronation is 0-4 deg in the neutral position.
    # A correction is considered mechanically successful if the post-orthotic
    # pronation angle returns to this range. Source: Kitaoka et al., Foot Ankle Int., 1997.

    before_L = before_metrics.get("pronation_angle_l_deg", 0.0)
    before_R = before_metrics.get("pronation_angle_r_deg", 0.0)

    after_L = after_metrics.get("pronation_angle_l_deg", 0.0)
    after_R = after_metrics.get("pronation_angle_r_deg", 0.0)

    delta_L = before_L - after_L
    delta_R = before_R - after_R

    print(f"Left Foot Delta: {delta_L:.2f} deg")
    print(f"Right Foot Delta: {delta_R:.2f} deg")

    def is_neutral(angle):
        return 0.0 <= angle <= 4.0

    validated = is_neutral(after_L) and is_neutral(after_R)

    nav_drop_L = after_metrics.get("navicular_drop_L_mm", 0.0)
    nav_drop_R = after_metrics.get("navicular_drop_R_mm", 0.0)

    if nav_drop_L > 10.0 or nav_drop_R > 10.0:
        print(
            f"WARNING: Navicular drop exceeds 10mm clinical safety threshold! (L: {nav_drop_L:.1f}mm, R: {nav_drop_R:.1f}mm)"
        )
        validated = False
    else:
        print(
            f"Navicular drop within safe limits (L: {nav_drop_L:.1f}mm, R: {nav_drop_R:.1f}mm)."
        )

    if validated:
        print(
            "CORRECTION VALIDATED: Pronation angle within neutral range (0-4 deg) and navicular drop safe."
        )
    else:
        print(
            "CORRECTION INCOMPLETE: Pronation angle outside neutral range or navicular drop unsafe. Clinician review required."
        )

    # Log back into db
    conn = sqlite3.connect(logger.db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN validation_comparison TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    validation_data = {
        "compared_to_session": after_id,
        "delta_L_deg": delta_L,
        "delta_R_deg": delta_R,
        "validated": validated,
    }

    cursor.execute(
        "UPDATE sessions SET validation_comparison = ? WHERE session_id = ?",
        (json.dumps(validation_data), before_id),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    p_run = subparsers.add_parser("run-pipeline")
    p_run.add_argument("video_path", default="demo.mp4", nargs="?")
    p_run.add_argument(
        "--height", type=float, default=1.75, help="Patient height in meters"
    )
    p_run.add_argument(
        "--scan-left", type=str, default=None, help="Path to 3D scan STL for left foot"
    )
    p_run.add_argument(
        "--scan-right",
        type=str,
        default=None,
        help="Path to 3D scan STL for right foot",
    )
    p_run.add_argument("--shoe-size", type=float, default=273.0, help="Shoe size in mm")

    p_gen = subparsers.add_parser("generate-cad")
    p_gen.add_argument("params_path")
    p_gen.add_argument("--stl")
    p_gen.add_argument("--json")
    p_gen.add_argument("--png")
    p_gen.add_argument("--scan-left", type=str, default=None)
    p_gen.add_argument("--scan-right", type=str, default=None)

    p_map = subparsers.add_parser("map-parameters")
    p_map.add_argument("video_path")
    p_map.add_argument("-o", "--output", required=True)
    p_map.add_argument(
        "--height", type=float, default=1.75, help="Patient height in meters"
    )

    p_comp = subparsers.add_parser("compare-sessions")
    p_comp.add_argument("before_id")
    p_comp.add_argument("after_id")

    args = parser.parse_args()

    if args.command == "generate-cad":
        generate_cad(
            args.params_path,
            args.stl,
            args.json,
            args.png,
            args.scan_left,
            args.scan_right,
        )
    elif args.command == "map-parameters":
        map_parameters(args.video_path, args.output, height_m=args.height)
    elif args.command == "compare-sessions":
        compare_sessions(args.before_id, args.after_id)
    else:
        # Fallback to run-pipeline
        run_pipeline(
            args.video_path if hasattr(args, "video_path") else "demo.mp4",
            height_m=args.height if hasattr(args, "height") else 1.75,
            scan_left=args.scan_left if hasattr(args, "scan_left") else None,
            scan_right=args.scan_right if hasattr(args, "scan_right") else None,
            shoe_size_mm=args.shoe_size if hasattr(args, "shoe_size") else 273.0,
        )
