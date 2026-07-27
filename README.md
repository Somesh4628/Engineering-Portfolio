# Engineering R&D Portfolio 🚀
### *Advanced Systems, Biomechanical CAD, & Embedded Edge Infrastructure*

[![GitHub Stars](https://img.shields.io/github/stars/Somesh4628/Engineering-Portfolio?style=for-the-badge&logo=github&color=gold)](https://github.com/Somesh4628/Engineering-Portfolio)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C%2B%2B-17-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)](https://isocpp.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![ESP32](https://img.shields.io/badge/ESP32-Dual%20Core-E7352C?style=for-the-badge&logo=espressif&logoColor=white)](https://www.espressif.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

Welcome to my personal engineering portfolio repository. This showcase features two publication-grade R&D software projects spanning **3D Parametric CAD Automation** and **Edge-Computing Industrial IoT (IIoT)** monitoring.

---

## 🌟 Featured Engineering Projects

| Project | Domain / Core Tech Stack | Key Technical Achievement | Documentation |
| :--- | :--- | :--- | :--- |
| 🦶 **Gaitform** | `Python`, `OpenCV`, `Trimesh`, `Streamlit` | Biomechanical 3D CAD pipeline generating custom orthotic STLs ($\pm 1.5\text{ mm}$ tolerance) from 1,260-node spatial pressure data. | [Gaitform Documentation](gaitform/README.md) |
| 🌊 **IntelliPipe** | `Python`, `C++`, `ESP32`, `PlatformIO`, `IIoT` | Edge IIoT pipeline monitoring system featuring an automated Python firmware factory & in-memory digital twin ($< 15\text{ ms}$ trip latency). | [IntelliPipe Documentation](MyPipelineApp/README.md) |

---

## 🔬 Project Summaries

### 1. [Gaitform](gaitform/README.md) — *Automated 3D Biomechanical CAD Pipeline*
* **Overview**: Translates raw 1,260-node spatial plantar pressure sensor matrices ($42 \times 30$ grid) into watertight, 3D-printable custom orthotic insoles. Incorporates 2D spatial Gaussian matrix filtering ($\sigma=1.8$) to eliminate vertex stress concentrations prior to additive manufacturing.
* **Tech Stack**: Python 3.10+, OpenCV, Trimesh, SciPy, Streamlit.
* **IP Notice**: Proprietary research prototype. Core heuristics, clinical decision rules, and model weights remain confidential.

---

### 2. [IntelliPipe](MyPipelineApp/README.md) — *Edge IIoT Monitoring & Firmware Factory*
* **Overview**: Deploys an in-memory digital twin running Welford's single-pass online variance algorithm directly on ESP32 microcontrollers for real-time leak detection. Features a Python firmware factory (`config_tool.py`) that dynamically compiles and flashes optimized C++ code.
* **Tech Stack**: C++17, Python 3.10+, ESP32, PlatformIO, IIoT MQTT.
* **IP Notice**: Patented technology. Digital twin architecture and firmware factory orchestration are protected under patent coverage.

---

## 📂 Repository Structure

```
Engineering-Portfolio/
├── gaitform/               # 🦶 Automated 3D Biomechanical CAD Pipeline
└── MyPipelineApp/          # 🌊 IntelliPipe Edge IIoT Monitoring & Firmware Factory
```

---

## 💻 Quick Setup

```bash
# Clone the portfolio repository
git clone https://github.com/Somesh4628/Engineering-Portfolio.git
cd Engineering-Portfolio

# Navigate to Gaitform
cd gaitform
pip install -r requirements.txt
streamlit run app.py

# Navigate to IntelliPipe
cd ../MyPipelineApp
pip install -r requirements.txt
python config_tool.py forge --directive directive.json
```

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.

---
*Created & Maintained by [Somesh](https://github.com/Somesh4628)*
