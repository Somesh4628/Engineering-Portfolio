import argparse
import json
import os
from gaitform.extraction import MediaPipeGaitExtractor
from gaitform.metrics.analyzer import GaitMetricsEngine
from gaitform.mapping.rules import OrthoticParameterMapper, RigidityZone, OrthoticParams
from gaitform.cad.generator import CADGenerator
from typing import Optional


def run_pipeline(
    video_path: str,
    height_m: float = 1.75,
    scan_path: Optional[str] = None,
    shoe_size_mm: float = 273.0,
):
    print(f"Running pipeline on {video_path} (Height: {height_m}m)")
    extractor = MediaPipeGaitExtractor()
    keypoints = extractor.extract(video_path)

    analyzer = GaitMetricsEngine(keypoints, patient_height_m=height_m)
    metrics = analyzer.analyze()

    mapper = OrthoticParameterMapper()
    params_dict = mapper.map_metrics_to_orthotic(metrics)

    generator = CADGenerator()
    mesh_left = generator.generate_mesh(
        params_dict["left"],
        foot_side="left",
        scan_path=scan_path,
        shoe_size_mm=shoe_size_mm,
    )
    mesh_right = generator.generate_mesh(
        params_dict["right"],
        foot_side="right",
        scan_path=scan_path,
        shoe_size_mm=shoe_size_mm,
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


def generate_cad(params_path, stl_base, json_base, png_base):
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

    generator = CADGenerator()
    mesh_left = generator.generate_mesh(left_params, foot_side="left")
    mesh_right = generator.generate_mesh(right_params, foot_side="right")

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    p_run = subparsers.add_parser("run-pipeline")
    p_run.add_argument("video_path", default="demo.mp4", nargs="?")
    p_run.add_argument(
        "--height", type=float, default=1.75, help="Patient height in meters"
    )
    p_run.add_argument("--scan", type=str, default=None, help="Path to 3D scan STL")
    p_run.add_argument("--shoe-size", type=float, default=273.0, help="Shoe size in mm")

    p_gen = subparsers.add_parser("generate-cad")
    p_gen.add_argument("params_path")
    p_gen.add_argument("--stl")
    p_gen.add_argument("--json")
    p_gen.add_argument("--png")

    args = parser.parse_args()

    if args.command == "generate-cad":
        generate_cad(args.params_path, args.stl, args.json, args.png)
    else:
        # Fallback to run-pipeline
        run_pipeline(
            args.video_path if hasattr(args, "video_path") else "demo.mp4",
            height_m=args.height if hasattr(args, "height") else 1.75,
            scan_path=args.scan if hasattr(args, "scan") else None,
            shoe_size_mm=args.shoe_size if hasattr(args, "shoe_size") else 273.0,
        )
