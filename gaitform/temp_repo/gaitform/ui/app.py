import streamlit as st
import os
import requests
import tempfile
from gaitform.extraction.mediapipe_extractor import MediaPipeGaitExtractor
from gaitform.metrics.analyzer import GaitMetricsEngine
from gaitform.mapping.rules import OrthoticParameterMapper
from gaitform.cad.generator import CADGenerator
from gaitform.photogrammetry.engine import PhotogrammetryEngine


def main():
    st.set_page_config(page_title="Gaitform - Professional UI", layout="wide")
    st.title("Gaitform Pipeline with Ecosystem Hub")

    st.sidebar.header("Configuration")
    hub_url = st.sidebar.text_input("Mobile Hub URL", value="http://localhost:8000")
    patient_height_m = st.sidebar.number_input(
        "Patient Height (m)", min_value=1.0, max_value=2.5, value=1.75, step=0.01
    )
    shoe_size_mm = st.sidebar.number_input(
        "Shoe Size (mm)", min_value=150.0, max_value=350.0, value=280.0, step=5.0
    )

    st.sidebar.header("Hub Uploads")
    available_videos = []
    available_scans = []
    try:
        res = requests.get(f"{hub_url}/api/uploads", timeout=2)
        if res.status_code == 200:
            uploads = res.json().get("uploads", [])
            available_videos = [f for f in uploads if f.endswith((".mp4", ".mov"))]
            available_scans = [f for f in uploads if f.endswith((".zip", ".rar"))]
            st.sidebar.success(f"Connected to Hub: {len(uploads)} files found.")
        else:
            st.sidebar.warning("Hub connected, but returned error.")
    except Exception:
        st.sidebar.error(f"Cannot connect to Hub at {hub_url}.")

    st.header("Step 1: Input Selection")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Gait Video")
        video_source = st.radio("Video Source", ["Upload File", "Select from Hub"])
        video_path = None
        uploaded_video = None
        if video_source == "Upload File":
            uploaded_video = st.file_uploader(
                "Upload Gait Video (.mp4)", type=["mp4", "mov"]
            )
        elif available_videos:
            selected_video = st.selectbox("Select Video from Hub", available_videos)
            try:
                hub_video_url = f"{hub_url}/api/uploads/{selected_video}"
                vid_res = requests.get(hub_video_url, timeout=5)
                if vid_res.status_code == 200:
                    temp_vid = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    temp_vid.write(vid_res.content)
                    temp_vid.close()
                    video_path = temp_vid.name
                    st.info(f"Successfully downloaded {selected_video} from Hub.")
                else:
                    st.error("Failed to download video from Hub.")
            except Exception:
                st.error("Error downloading video from Hub.")
        else:
            st.warning("No videos on Hub.")

    with col2:
        st.subheader("Photogrammetry Scan")
        scan_source = st.radio("Scan Source", ["Upload ZIP", "Select from Hub"])
        if scan_source == "Upload ZIP":
            _ = st.file_uploader("Upload Photos (.zip)", type=["zip"])
        elif available_scans:
            selected_scan = st.selectbox("Select Scan from Hub", available_scans)
            st.info(f"Selected {selected_scan} from Hub.")
        else:
            st.warning("No scans on Hub.")

    if st.button("Run Pipeline"):
        if video_source == "Upload File" and uploaded_video is not None:
            # Save uploaded video to temp file
            temp_vid = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_vid.write(uploaded_video.read())
            temp_vid.close()
            video_path = temp_vid.name
        elif video_source == "Upload File" and uploaded_video is None:
            # For testing with the sample video
            video_path = "sample_data/demo.mp4"
            st.info("No video uploaded, using sample_data/demo.mp4 for demonstration.")
            if not os.path.exists(video_path):
                st.error("Sample video not found.")
                return

        try:
            with st.spinner("Phase 1: Pose Extraction..."):
                extractor = MediaPipeGaitExtractor()
                seq = extractor.extract(video_path)
                if len(seq.frames) < 30:
                    st.error(
                        "Video must contain at least 30 valid frames with detected pose landmarks. "
                        "Try a longer or clearer video.")
                    st.stop()
                st.success(f"Extracted {len(seq.frames)} frames.")

            with st.spinner("Phase 2: Metrics Analysis..."):
                engine = GaitMetricsEngine(seq, patient_height_m=patient_height_m)
                metrics = engine.analyze()
                st.json(metrics)

            with st.spinner("Phase 3: Orthotic Parameter Mapping..."):
                mapper = OrthoticParameterMapper()
                metrics["foot_length_mm"] = shoe_size_mm
                params_dict = mapper.map_metrics_to_orthotic(metrics)

                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown("### Left Foot")
                    st.json(params_dict["left"].to_dict())
                    for flag in params_dict["left"].flags_for_review:
                        st.warning(f"Flag: {flag}")
                with col_r:
                    st.markdown("### Right Foot")
                    st.json(params_dict["right"].to_dict())
                    for flag in params_dict["right"].flags_for_review:
                        st.warning(f"Flag: {flag}")

            with st.spinner("Phase 4: Photogrammetry (Mock)..."):
                photo_engine = PhotogrammetryEngine()
                scan_out_path = "temp_extract/scan_mock.stl"
                os.makedirs("temp_extract", exist_ok=True)
                photo_engine.process_video_to_stl(video_path, scan_out_path)
                st.success("Photogrammetry complete.")

            with st.spinner("Phase 5: CAD Generation..."):
                cad_gen = CADGenerator()
                mesh_l = cad_gen.generate_mesh(
                    params_dict["left"],
                    foot_side="left",
                    shoe_size_mm=shoe_size_mm,
                    scan_path=scan_out_path,
                )
                mesh_r = cad_gen.generate_mesh(
                    params_dict["right"],
                    foot_side="right",
                    shoe_size_mm=shoe_size_mm,
                    scan_path=scan_out_path,
                )

                mesh_l.export("left_orthotic.stl")
                mesh_r.export("right_orthotic.stl")

                st.success("CAD generation complete. STLs exported.")

                png_l = cad_gen.generate_zoning(
                    params_dict["left"],
                    "left_zoning.json",
                    "left_zoning.png",
                    foot_side="left")
                png_r = cad_gen.generate_zoning(
                    params_dict["right"],
                    "right_zoning.json",
                    "right_zoning.png",
                    foot_side="right")

                col_img_l, col_img_r = st.columns(2)
                with col_img_l:
                    st.image(png_l, caption="Left Foot Rigidity Zones Heatmap")
                with col_img_r:
                    st.image(png_r, caption="Right Foot Rigidity Zones Heatmap")

        finally:
            if (
                video_source == "Upload File"
                and uploaded_video is not None
                and video_path
            ):
                os.remove(video_path)


if __name__ == "__main__":
    main()
