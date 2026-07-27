# Gaitform 🦶⚡
### *Automated 3D Biomechanical CAD Pipeline for Custom Orthotics*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![Trimesh](https://img.shields.io/badge/Trimesh-3.23%2B-FF6F61?style=for-the-badge&logo=geometry&logoColor=white)](https://trimesh.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tolerance](https://img.shields.io/badge/Dimensional%20Tolerance-%C2%B11.5%20mm-brightgreen?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

> 🔒 **PROPRIETARY RESEARCH & DEMONSTRATION NOTICE**  
> *Gaitform is an R&D demonstration prototype. Core proprietary heuristics, clinical decision parameters, and raw model weights remain confidential. This repository provides high-level functional architecture, matrix processing standards, and UI visualization tools.*

---

## 📌 Executive Summary

**Gaitform** is an automated biomechanical CAD generation pipeline that bridges spatial plantar pressure diagnostics with direct additive manufacturing. The system ingests raw **1,260-node spatial plantar pressure matrices** (derived from clinical sensor arrays or vision-based pressure estimation), performs spatial matrix interpolation, maps pressure concentrations to structural deformities, and procedurally generates custom, watertight **3D-printable orthotic shells** (STL/OBJ).

Engineered to strict clinical manufacturing criteria, Gaitform maintains a **dimensional tolerance of $\pm 1.5\text{ mm}$** across the footbed profile while incorporating dynamic surface optimization to eliminate stress concentrations prior to 3D printing.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A[Raw 1,260-Node Pressure Data] --> B[Data Ingestion & Matrix Parser]
    B --> C[OpenCV Spatial Matrix Reconstruction]
    C --> D[2D Grid Interpolation]
    D --> E[Biomechanical Parameter Mapping]
    E --> F[Trimesh Parametric Shell Generation]
    F --> G[Surface Optimization & Vertex Smoothing]
    G --> H[Watertight Mesh Validation & Tolerance Check]
    H --> I[Streamlit Interactive Dashboard]
    H --> J[Production-Ready STL Export]
```

---

## 🛠️ Tech Stack & Dependencies

| Component | Library / Framework | Technical Purpose |
| :--- | :--- | :--- |
| **Language** | `Python 3.10+` | Core execution environment & numerical pipeline |
| **Matrix Processing** | `OpenCV (cv2)`, `NumPy` | Grid interpolation, spatial pressure heatmap synthesis |
| **3D CAD Generation** | `Trimesh`, `SciPy` | Parametric mesh construction, normal vector offset, STL serialization |
| **GUI & Visualization** | `Streamlit`, `Plotly` | Real-time interactive dashboard, 3D viewport, pressure visualizer |
| **Spatial Analysis** | `SciPy.ndimage` | Spatial kernel convolution & boundary conditions |

---

## 🔬 High-Level Mathematical Surface Optimization

To prevent localized stress fractures during walking and eliminate layer-adhesion defects during 3D printing, Gaitform applies spatial Gaussian filtering over the raw pressure topology before parametric mesh displacement.

### 1. Spatial Kernel Surface Smoothing
The spatial smoothing matrix $G(x, y)$ is calculated over a discrete neighborhood kernel size $k \times k$:

$$G(x, y) = \frac{1}{2\pi\sigma^2} \exp\left(-\frac{x^2 + y^2}{2\sigma^2}\right)$$

### 2. Mesh Vertex Displacement
Each base mesh vertex $\mathbf{v}_i = (x_i, y_i, z_i)^T$ is translated along its vertex unit normal vector $\hat{\mathbf{n}}_i$:

$$\mathbf{v}_i' = \mathbf{v}_i + \left( h_{\text{base}} + \alpha \cdot Z_{\text{smooth}}(u, v) \right) \hat{\mathbf{n}}_i$$

enforcing the strict manufacturing boundary:

$$\max_{\mathbf{v}} \|\mathbf{v}_{\text{generated}} - \mathbf{v}_{\text{nominal}}\| \le 1.5\text{ mm}$$

---

## ⚡ Key Technical Features

1. **Data Ingestion & Matrix Processing**: Parses raw 1,260-node spatial sensor matrices ($42 \times 30$ grid) and performs matrix filtering.
2. **Parametric Geometry Generation**: Procedurally computes custom footbed geometry mapped to heel strike, arch support, and metatarsal zones.
3. **Surface Optimization Algorithm**: Regularizes vertex offsets to prevent step-discontinuities and stress boundaries.
4. **Interactive Streamlit Dashboard**: Live interactive 3D mesh preview, adjustable parameters, and one-click STL export.

---

## 💻 Installation & Usage Guide

```bash
# Clone the repository
git clone https://github.com/Somesh4628/Engineering-Portfolio.git
cd Engineering-Portfolio/gaitform

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit Dashboard
streamlit run app.py
```

---

## 📜 License & IP Notice

Distributed under the **MIT License**. Core proprietary algorithms, clinical rules, and model weights remain confidential. See `LICENSE` for details.

---
*Maintained by [Somesh](https://github.com/Somesh4628) • R&D Engineering Portfolio*
