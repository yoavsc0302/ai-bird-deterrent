# AI Bird Deterrent Project

This project utilizes the Hailo-8L AI accelerator on a Raspberry Pi 5 to perform person detection and tracking.

## Hardware Requirements

- Raspberry Pi 5
- Hailo-8L AI Accelerator
- Raspberry Pi Camera Module 3

## Directory Structure

```
ai-bird-deterrent/
├── basic_pipelines/     # Core detection code
├── logs/               # Log files
├── resources/          # AI models and libraries
├── scripts/           # Setup and utility scripts
└── README.md
```

## Initial Setup

### 1. Environment Setup

First, you need to activate the Hailo virtual environment. This is crucial for all operations:

```bash
source scripts/setup_env.sh
```

You should see `(venv_hailo_rpi5_examples)` in your terminal prompt after activation. All subsequent commands must be run with this environment active.

### 2. Installation

Run the installation script to set up dependencies:

```bash
./scripts/install.sh
```

This script will:
- Install required Python packages
- Install system dependencies
- Download necessary model files

### 3. Download Resources

The installation script should handle this automatically, but if you need to download resources manually:

```bash
./scripts/download_resources.sh
```

This downloads:
- YOLOv8s model for Hailo-8L
- YOLOv8s pose estimation model
- Required post-processing libraries

### 4. Post-Processing Setup (If Needed)

The post-processing library is essential for converting raw model output into meaningful detections. If you need to compile it:

```bash
./scripts/compile_postprocess.sh
```

Note: This is typically only needed during initial setup or if you modify the post-processing code.

## Running the Application

1. Make sure the environment is activated:
```bash
source scripts/setup_env.sh
```

2. Run the detection application:
```bash
python basic_pipelines/detection.py
```

The application will:
- Initialize the Raspberry Pi camera
- Load the YOLOv8s model
- Start detecting people in real-time
- Display the video feed with detections

## Models

The project includes these key models:
- `yolov8s_h8l.hef`: Main detection model
- `yolov8s_pose_h8l.hef`: Pose estimation model (for future tracking features)

## Troubleshooting

1. If you see "No such file" errors:
   - Ensure you've run the download_resources.sh script
   - Check that all files exist in the resources/ directory

2. If you get Hailo-related errors:
   - Make sure the environment is activated
   - Verify the Hailo-8L is properly connected
   - Check the logs/ directory for detailed error messages

3. If the camera isn't working:
   - Ensure the camera module is properly connected
   - Check that the camera is enabled in raspi-config

## Important Notes

1. Always run scripts from the project root directory
2. Keep the virtual environment activated during all operations
3. Check the logs directory for troubleshooting information
4. The post-processing library compilation (compile_postprocess.sh) is usually only needed once during initial setup

## Future Features

The project is designed to support:
- Person tracking with unique IDs
- Movement analysis
- Pose estimation