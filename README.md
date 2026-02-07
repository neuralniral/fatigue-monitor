### 📄 Project Summary

The Real-Time Fatigue Monitoring System is an integrated hardware-software solution designed to monitor user drowsiness and combat this through active cognitive engagement. By utilizing MediaPipe's facial landmark tracking to monitor Eye Aspect Ratio (EAR), a measure of how closed the eyes are, the system identifies fatigue in real time. This project implements a "Human-in-the-Loop" (HIL) verification process via an Arduino-based joystick interface, requiring the driver to perform a specific directional task to prove alertness, with an alarm triggered upon failure. The system additionally maintains a robust data-logging architecture that tracks alertness (joystick activity), reaction latency, and total incident duration. Future iterations could plot this data to observe "micro-sleep" patterns.

---

# 🛡️ Real-Time Fatigue Monitoring System

**An AI-driven safety interface combining Computer Vision and Hardware-in-the-Loop (HIL) feedback.**

## 📌 Project Overview

This system is designed to detect driver drowsiness using the **Eye Aspect Ratio (EAR)** method. It incorporates an **Awareness Activity**: when drowsiness is detected, the user must perform a physical task using an Arduino-linked joystick to prove alertness and silence the alarm.

### Key Features

* **Facial Landmark Tracking:** Powered by MediaPipe Face Mesh.
* **Time-Based Detection:** Monitors eye closure in seconds (independent of CPU frame rate).
* **Physical Challenge-Response:** Requires specific joystick movements (UP, DOWN, LEFT, RIGHT).
* **Comprehensive Data Logging:** Captures reaction times and total incident duration to a CSV.
* **Cross-Platform Portability:** Uses relative pathing for seamless deployment across different machines.

---

## 📂 Project Structure

```
Fatigue-Monitor/
├── README.md
├── requirements.txt
├── .gitignore
├── control-data/          # (ignored) test videos and raw data
├── outputs/               # (ignored) generated CSV logs
├── sounds/                # Audio assets
└── source-code/           # Python and Arduino source code
    ├── FM_main.py         # Main fatigue monitoring script
    ├── awareness_activity.py  # Awareness activity class
    ├── face_landmarker.task   # MediaPipe model file (binary)
    └── joystick_firmware/
        └── joystick_firmware.ino  # Arduino joystick code
```

---

## 📐 EAR Formula

The openness of the eye is calculated using Euclidean distances between eyelid landmarks. Defaults in `FM_main.py`:

- Drowsy threshold: 0.20 EAR
- Recovery threshold: 0.25 EAR
- Drowsy trigger time: 2.5 seconds

---

## ⚙️ Setup & Installation

### Hardware

- Arduino Uno/Nano + analog joystick
- Webcam (USB or integrated)

### Software

1. Install Python 3.10 or newer.
2. From the project root, install dependencies:

```bash
pip install -r requirements.txt
```

3. Flash the Arduino sketch in `source-code/joystick_firmware/` to your board.

---

## 🚀 Usage

1. Connect the Arduino via USB (default port `COM3`, adjustable in code).
2. Change into the `source-code/` directory and run:

```bash
python FM_main.py
```

Operational notes:

- Normal: EAR > 0.25 (green HUD)
- Drowsy: EAR < 0.20 (red HUD, timer starts)
- Activity: After 2.5s, complete the joystick prompt to silence the alarm
- Recovery resets once EAR > recovery threshold

---

## 📊 Data Logging

Events are appended to `outputs/fatigue_results.csv` with columns:

```
Timestamp,Event,EAR,Reaction_Time,Duration
```

Note: `control-data/` and `outputs/` are ignored by `.gitignore` and are not included in the repository by default.

---

## 📄 License

This repository includes an `LICENSE` file (MIT) — see `LICENSE` for details.

---
