# src/test_servo.py

from servo_control import PanTiltController

def test_servo():
    pan_tilt = PanTiltController()
    pan_tilt.center()
    print(f"Pan Servo Position: {pan_tilt.pan_servo.angle}°")
    print(f"Tilt Servo Position: {pan_tilt.tilt_servo.angle}°")
    pan_tilt.cleanup()

if __name__ == "__main__":
    test_servo()
