# AI Bird Deterrent System

This project implements an AI-powered bird deterrent system using person detection and tracking. The system uses a Hailo ML accelerator for efficient inference, along with servo motors for pan/tilt control and a laser for targeting.

## Project Structure

```
ai-bird-deterrent/
├── config.yaml           # Main configuration file
├── logs/                 # Log files directory
├── resources/           # Model and resource files
│   ├── yolov8s_h8l.hef
│   └── libyolo_hailortpp_postprocess.so
├── scripts/             # Installation and setup scripts
├── src/                # Source code
│   ├── config.py       # Configuration management
│   ├── hailo_detection_app.py  # Main detection application
│   ├── laser_control.py        # Laser control module
│   ├── person_tracker.py       # Person tracking logic
│   └── servo_control.py        # Pan/tilt servo control
└── tests/              # Test files
```

## Requirements

- Raspberry Pi (tested on RPi 4)
- Hailo-8 or Hailo-8L ML accelerator
- Pan/tilt servo mechanism
- Laser module
- PCA9685 PWM controller for servos
- Camera module

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-bird-deterrent.git
cd ai-bird-deterrent
```

2. Run the installation script:
```bash
./scripts/install.sh
```

3. Set up the environment:
```bash
source scripts/setup_env.sh
```

## Configuration

The system is configured through `config.yaml`. Key configuration sections include:

- `paths`: Resource and model file locations
- `camera`: Camera settings
- `detection`: Detection and tracking parameters
- `servo`: Servo motor configuration
- `laser`: Laser control settings
- `fov`: Camera field of view settings

Example configuration modifications:
```yaml
# Adjust servo sensitivity
servo:
  pan:
    threshold: 2.0  # Larger value = less sensitive
  tilt:
    threshold: 2.0

# Modify detection confidence
detection:
  nms_score_threshold: 0.4  # Higher = more confident detections
```

## Usage

1. Ensure all hardware is properly connected
2. Modify config.yaml as needed
3. Run the application:
```bash
python -m src.main
```

Optional arguments:
- `--config`: Specify an alternative configuration file path

## Hardware Setup

### Servo Configuration
- Pan servo: Connected to PCA9685 channel 0
- Tilt servo: Connected to PCA9685 channel 1
- I2C address: 0x40 (configurable)

### Laser Setup
- Connected to GPIO pin 13 (configurable)
- Uses gpiod for control

## Development

### Adding New Features

1. Update config.yaml with any new parameters
2. Implement new functionality in appropriate module
3. Update main application class as needed
4. Add tests for new functionality

### Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Troubleshooting

Common issues and solutions:

1. Servo Jitter
   - Adjust servo thresholds in config.yaml
   - Check power supply stability

2. Detection Issues
   - Adjust nms_score_threshold in config.yaml
   - Verify camera setup and lighting

3. Laser Control
   - Verify GPIO permissions
   - Check physical connections

## License

[Your License Here]

## Acknowledgments

- Hailo for ML acceleration support
- [Other acknowledgments]