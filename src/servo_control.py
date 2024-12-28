# src/servo_control.py

import time
import json
import os
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import board
import busio

SERVO_LIMITS = {
    'PAN': {'MIN': -90, 'MAX': 90},
    'TILT': {'MIN': -90, 'MAX': 90}
}

class PanTiltController:
    def __init__(
        self, 
        pan_channel=0,
        tilt_channel=1,
        pan_limits=(SERVO_LIMITS['PAN']['MIN'], SERVO_LIMITS['PAN']['MAX']),
        tilt_limits=(SERVO_LIMITS['TILT']['MIN'], SERVO_LIMITS['TILT']['MAX']),
        i2c_address=0x40
    ):
        # Initialize I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=i2c_address)
        self.pca.frequency = 50
        
        # Initialize servos
        self.pan_servo = servo.Servo(self.pca.channels[pan_channel])
        self.tilt_servo = servo.Servo(self.pca.channels[tilt_channel])
        
        # Load calibration
        self.config_file = 'servo_calibration.json'
        self.load_calibration()
        
        # Store limits
        self.pan_limits = pan_limits
        self.tilt_limits = tilt_limits
        
        # Current relative positions
        self.current_pan = 0
        self.current_tilt = 0
        
        # Move to center
        self.center()
    
    def load_calibration(self):
        """Load calibration from a JSON file."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.pan_center = config.get('pan_center', 70)  # Default to calibrated center of 70
                self.tilt_center = config.get('tilt_center', 74)  # Default to calibrated center of 74
                print(f"Loaded calibration: pan={self.pan_center}, tilt={self.tilt_center}")
        else:
            self.pan_center = 70  # Calibrated center
            self.tilt_center = 74  # Calibrated center
            print("No calibration file found, using calibrated centers: pan=70, tilt=74")

    def _constrain_angle(self, angle, limits):
        """Constrain angle to [MIN..MAX]."""
        return max(min(angle, limits[1]), limits[0])
    
    def move(self, pan_angle, tilt_angle):
        """
        Move the servos to the specified angles (relative to center).
        E.g., pan_angle=0 => the servo center, +90 => full right, -90 => full left.
        """
        # Constrain
        pan_angle = self._constrain_angle(pan_angle, self.pan_limits)
        tilt_angle = self._constrain_angle(tilt_angle, self.tilt_limits)
        
        # Add angles to calibrated centers
        servo_pan = self.pan_center + pan_angle
        servo_tilt = self.tilt_center + tilt_angle
        
        # Physical servo range is typically [0..180]
        servo_pan = min(max(servo_pan, 0), 180)
        servo_tilt = min(max(servo_tilt, 0), 180)
        
        # Move
        try:
            self.pan_servo.angle = servo_pan
            self.tilt_servo.angle = servo_tilt
            self.current_pan = pan_angle
            self.current_tilt = tilt_angle
            print(f"Moved to servo_pan={servo_pan}°, servo_tilt={servo_tilt}°")
        except ValueError as e:
            print(f"Error moving servos: {e}")
    
    def center(self):
        """Center the servos (0,0 relative)."""
        print("Centering servos...")
        self.move(0, 0)

    def get_position(self):
        return (self.current_pan, self.current_tilt)
    
    def cleanup(self):
        """Cleanup resources"""
        self.pca.deinit()