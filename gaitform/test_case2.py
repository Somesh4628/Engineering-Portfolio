import sys
import trimesh
from gaitform.extraction.mediapipe_extractor import MediaPipeGaitExtractor
from gaitform.metrics.analyzer import GaitMetricsEngine
from gaitform.mapping.rules import OrthoticParameterMapper
from gaitform.cad.generator import CADGenerator

video_path = "sample_data/demo.mp4"
extractor = MediaPipeGaitExtractor()
keypoints = extractor.extract(video_path)
analyzer = GaitMetricsEngine(keypoints, patient_height_m=1.75)
metrics = analyzer.analyze()
mapper = OrthoticParameterMapper()
params_dict = mapper.map_metrics_to_orthotic(metrics)

mesh = trimesh.load("temp_extract/test_scan.stl")
gen = CADGenerator()
out = gen.generate_mesh(params_dict["left"], scan_mesh=mesh, foot_side="left")
print("FLAGS FOR REVIEW:", params_dict["left"].flags_for_review)
