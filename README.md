# AI Bird Deterrent System

A computer vision system that uses YOLOv8 and DeepSort to detect and track people using a Raspberry Pi camera. This system is designed to be part of a bird deterrent solution.

## Hardware Requirements
- Raspberry Pi (tested on Raspberry Pi 4)
- Raspberry Pi Camera Module

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-bird-deterrent.git
cd ai-bird-deterrent
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Download YOLOv8 model:
The `yolov8n.pt` model should be placed in the `models/` directory.

## Project Structure
```
AI-BIRDDETERENT/
│
├── models/
│   └── yolov8n.pt
├── scripts/
│   └── person_tracking.py
├── venv/
├── .gitignore
├── README.md
└── requirements.txt
```

## Usage

1. Activate the virtual environment:
```bash
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Run the person tracking script:
```bash
python scripts/person_tracking.py
```

3. Press 'q' to quit the application.

## Features
- Real-time person detection using YOLOv8
- Person tracking with DeepSort algorithm
- Visual display of tracking results with bounding boxes and ID numbers

## Troubleshooting
If you encounter any camera-related issues:
1. Ensure the Raspberry Pi camera is properly connected
2. Enable the camera interface using `raspi-config`
3. Verify camera permissions

## License
[Your chosen license]

## Contributing
[Your contribution guidelines]