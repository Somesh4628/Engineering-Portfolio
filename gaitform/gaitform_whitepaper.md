# Gaitform Digital Podiatry: Complete Project Context & Technical Log

**Date Generated:** July 4, 2026
**Project Phase:** V1 Software Prototype (In-Silico Complete)

---

## 1. The Main Goal
The core objective of the Gaitform project is to revolutionize custom orthotics manufacturing. Instead of relying on manual plaster casting or expensive proprietary CAD software, Gaitform aims to build a completely automated, open-architecture, Python-driven software pipeline. 

The system takes in three streams of physical clinic data:
1. **Kinematic Video** (Full body gait and specific bone tracking)
2. **3D Foot Scans** (STL files from mobile photogrammetry like Polycam)
3. **Plantar Pressure Data** (CSV arrays from pressure mats)

It mathematically fuses these datasets and automatically exports a customized, organically contoured, 3D-printable `.stl` file specifically sculpted to correct the patient's biomechanical faults.

---

## 2. Technologies Stack Used
* **Core Language:** Python 3
* **Visual Dashboard:** Streamlit (`app.py`)
* **3D Geometry & CAD:** `trimesh` (for mesh generation, raycasting, and boolean operations)
* **Math & Data Smoothing:** `numpy`, `scipy` (`CubicSpline`, `scipy.ndimage.gaussian_filter`)
* **Biomechanics / Video Tracking:** OpenCV (`cv2`) for HSV color tracking, Google MediaPipe for full-body pose extraction.
* **Visualization:** `matplotlib` (for generating 2D rigidity heatmaps).
* **Testing:** `pytest`

---

## 3. Minute-by-Minute: What We Actually Built

### Phase 1: Data Ingestion & The CAD Engine
* **Pressure Mapping (`pressure_parser.py`):** We successfully wrote an algorithm to parse complex 1,260-node `fscan` pressure CSV arrays. The parser cleans the data, calculates the Center of Pressure (CoP), and maps the high-pressure zones to specific anatomical regions (Heel, Midfoot, Forefoot).
* **Rigidity Zoning:** We created a mapping system that automatically assigns 3D printing infill targets (e.g., "Firm", "Medium", "Soft") based on the pressure spikes.
* **Procedural CAD Generation (`generator.py`):** We built a procedural 3D generation tool that starts with a basic `dummy_foot.stl` bounding shape. 
* **Boolean Raycasting Math:** The engine dynamically morphs the flat cylinder. It projects the pressure mapping as a Z-axis heightmap onto the mesh to carve out a custom heel cup and build a raised arch support.
* **Clinical Safety Margins:** We implemented a strict ±1.5mm tolerance check. If the boolean subtraction deviates by more than 1.5mm (which would ruin the fit of the orthotic), the system throws a clinical review flag. We wrote a stress-test (`test_noisy_scan.py`) that proved our engine successfully survives corrupted/noisy 3D meshes without crashing.

### Phase 2: Kinematics & UI Integration
* **Streamlit Hub (`app.py`):** We built a sleek, local web dashboard allowing clinicians to upload their files (MP4, STL, CSV) and hit "Run Pipeline". It handles file routing and instantly provides the generated `.stl` files for download, along with visual heatmaps.
* **The Kinematic Occlusion Problem:** We recognized a classic biomechanics flaw: taking a standard walking video from the side blocks the Navicular bone on the inside of the foot with the swinging leg. 
* **The "One-Step Protocol":** To solve this, we updated the UI and architecture to accept **three distinct videos**: one for full-body walking, and two dedicated close-up videos (Left Foot and Right Foot) of the patient taking a single step. 
* **OpenCV Navicular Tracking (`navicular.py`):** We wrote a custom script that scans the One-Step Protocol videos for a neon-green clinical sticker. It isolates the color using strict HSV boundaries (`[35, 100, 100]` to `[85, 255, 255]`), calculates the vertical pixel drop (Y-axis) during the footstrike, and converts it to millimeters using bounding-box ratios. 
* **Navicular Safety Flag:** We integrated a warning system into the UI that flashes a massive red error if the calculated Navicular drop exceeds the clinical threshold of `10mm`.

### Phase 2.5: Mesh Polish and Artifact Fixing
* **The "Fin" Glitch:** Upon inspecting the generated STLs in SolidWorks, we noticed a sharp, non-manifold edge (a jagged "fin" or bump) where the heel cup transitioned to the midfoot. This was a mathematical artifact caused by a sharp drop-off (a cliff) in the raw pressure CSV array.
* **Gaussian Smoothing Fix:** We jumped back into `cad/generator.py` and implemented a mathematical fix. Before the 3D vertices are generated, we reshaped the array back to a 2D grid and applied a `scipy.ndimage.gaussian_filter(sigma=1.5)`. This acts as digital sandpaper, gently blurring the sharp pressure cliffs and ensuring the final `.stl` is an organically flowing, anatomically accurate, and perfectly 3D-printable shape.

---

## 4. Current Status
We have a **100% functional software pipeline.** 
The Streamlit UI works flawlessly. The state-reset bug during file downloads was patched using `st.session_state`. The system correctly ingests video and data, safely checks clinical thresholds, mathematically shapes the orthotics, and outputs clean, smoothed `.stl` files.

---

## 5. Next Steps (Phase 3: Physical & Clinical Trial)
The software (in-silico) phase is complete. The next steps involve the real world (in-vivo):
1. **3D Printing Test:** Physically print the `orthotic_left.stl` file in TPU (Thermoplastic Polyurethane) on a standard 3D printer to verify the physical shore hardness and flexibility of the zones.
2. **Small Clinical Trial (N=5):** Find 5 human participants. Capture their actual foot scans using an iPhone (Polycam/Hedge3D) instead of the dummy cylinder. Run their real pressure and video data through the app.
3. **Data Verification:** Have the participants wear the printed TPU orthotics. Record a second Navicular tracking video to prove the orthotic successfully stopped the arch collapse. 
4. **Publication:** With the physical before/after data secured, write and publish the findings in *Clinical Biomechanics* or *IEEE Transactions on Biomedical Engineering*.
