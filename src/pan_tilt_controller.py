import time
from typing import Tuple
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import board
import busio
import logging

'''
Important to note:
PCA9685 is a PWM controller that can control up to 16 servos. This board connects between the Raspberry Pi and the servos,
and allows the Raspberry Pi to control the servos using PWM signals.
'''

class PanTiltController:
    def __init__(
        self,
        config: dict  # Pass the 'servo' section of our config
    ):
        """
        Initialize the pan/tilt servo controller.
        
        Args:
            config (dict): Configuration dictionary containing servo settings:
                - pan: channel, center, min_angle, max_angle
                - tilt: channel, center, min_angle, max_angle
                - i2c_address: I2C address of PCA9685
        """
        try:
            # Extract configuration
            servo_config = config['servo']  # Get servo-specific config
            self.pan_config = servo_config['pan']
            self.tilt_config = servo_config['tilt']
            self.i2c_address = servo_config['i2c_address']
            
            # Get FOV from main config
            self.fov = config['fov'] # Field of view (FOV) of the camera in degrees (horizontal, vertical) 
            
            # Initialize I2C communication with PCA9685
            i2c = busio.I2C(board.SCL, board.SDA) # Initialize I2C bus (I2C is a serial communication protocol used for the Raspberry Pi to communicate with PCA9685)
            self.pca = PCA9685(i2c, address=self.i2c_address) # Initialize PCA9685 with I2C bus and address
            self.pca.frequency = 50  # Servos typically operate at 50Hz
            
            # Initialize servos
            self.pan_servo = servo.Servo(self.pca.channels[self.pan_config['channel']]) # channel is the PWM channel on the PCA9685, among 16 channels
            self.tilt_servo = servo.Servo(self.pca.channels[self.tilt_config['channel']]) # channel is the PWM channel on the PCA9685, among 16 channels
            
            # Store configurations
            self.pan_limits = (self.pan_config['min_angle'], self.pan_config['max_angle'])
            self.tilt_limits = (self.tilt_config['min_angle'], self.tilt_config['max_angle'])
            
            # Store centers
            self.pan_center = self.pan_config['center']
            self.tilt_center = self.tilt_config['center']
            
            # Current relative positions
            self.current_pan = 0
            self.current_tilt = 0
            
            logging.info(f"Pan/Tilt controller initialized with:")
            logging.info(f"  Pan: channel={self.pan_config['channel']}, center={self.pan_center}")
            logging.info(f"  Tilt: channel={self.tilt_config['channel']}, center={self.tilt_center}")
            
            # Move to center position
            self.center()
            
        except Exception as e:
            logging.error(f"Failed to initialize pan/tilt controller: {e}")
            raise

    def _constrain_angle(self, angle: float, limits: tuple) -> float:
        """
        Constrain angle to [MIN..MAX].

        # Ensure angle is within the limits, so for example:
        # - if angle is 100, it will be set to 90 (max)
        # - if angle is -100, it will be set to -90 (min)
        # - if angle is 60 (within limits), it will remain 60
        
        Args:
            angle (float): Input angle
            limits (tuple): (min_angle, max_angle)
            
        Returns:
            float: Constrained angle
        """
        return max(min(angle, limits[1]), limits[0]) 
    
    def move(self, pan_angle: float, tilt_angle: float):
        """
        Move the servos to the specified angles relative to center.
        
        Args:
            pan_angle (float): Pan angle relative to center (negative=left, positive=right)
            tilt_angle (float): Tilt angle relative to center (negative=down, positive=up)
            
        Example:
            pan_angle=0: center position
            pan_angle=90: full right
            pan_angle=-90: full left
        """
        try:
            # Constrain angles to limits
            pan_angle = self._constrain_angle(pan_angle, self.pan_limits)
            tilt_angle = self._constrain_angle(tilt_angle, self.tilt_limits)
            
            # Add angles to calibrated centers
            new_pan_angle = self.pan_center + pan_angle
            new_tilt_angle = self.tilt_center + tilt_angle
            
            # Ensure within physical servo range [0..180]
            # (servo angle is limited to 0-180 degrees, its different for the _constrain_angle function which is used to limit the pan and tilt angles to prevent cabels from getting tangled)
            new_pan_angle = min(max(new_pan_angle, 0), 180) 
            new_tilt_angle = min(max(new_tilt_angle, 0), 180)
            
            # Move servos
            self.pan_servo.angle = new_pan_angle # Set the angle of the servo, angle is a property of the servo class imported from adafruit_motor
            self.tilt_servo.angle = new_tilt_angle 
            
            # Update current positions
            self.current_pan = pan_angle
            self.current_tilt = tilt_angle
            
            logging.debug(f"Moved to servo_pan={new_pan_angle}°, servo_tilt={new_tilt_angle}°")
            
        except ValueError as e:
            logging.error(f"Error moving servos: {e}")
            raise
    
    def center(self):
        """Center both servos (move to 0,0 relative position)."""
        logging.info("Centering servos...")
        self.move(0, 0)

    def get_position(self) -> tuple:
        """
        Get current servo positions.
        
        Returns:
            tuple: (current_pan_angle, current_tilt_angle)
        """
        return (self.current_pan, self.current_tilt)
    
    def _apply_nonlinear_transform(self, value: float, power: float) -> float:
        """
        Apply non-linear power transformation to coordinate values while preserving sign.
        
        This transformation improves tracking precision by:
        - Reducing movement for small deviations (more precise control near center)
        - Amplifying movement for large deviations (faster response near edges)
        
        Args:
            value: Input value in range [-1, 1]
            power: Power factor for non-linear scaling (>1 reduces small movements)
            
        Returns:
            float: Transformed value, maintaining original sign
        """
        import math
        return math.copysign(math.pow(abs(value), power), value)
    
    def calculate_angles(self, center_x: float, center_y: float) -> Tuple[float, float]:
            """
            Calculate servo angles based on detection center coordinates using tangent-based calculation
            with aggressive scaling for more responsive movement. Different scaling for pan and tilt.
            
            Args:
                center_x (float): Normalized x coordinate (0-1)
                center_y (float): Normalized y coordinate (0-1)
                
            Returns:
                Tuple[float, float]: Calculated (pan_angle, tilt_angle)
            """
            import math
            
            # Normalize coordinates to [-1, 1]
            x_deviation = (center_x - 0.5) * 2  
            y_deviation = (center_y - 0.5) * 2
            
            # Apply non-linear transformations to improve tracking precision and responsiveness
            x_deviation = self._apply_nonlinear_transform(x_deviation, self.pan_config.get('power_factor', 1.5))
            y_deviation = self._apply_nonlinear_transform(y_deviation, self.tilt_config.get('power_factor', 1.3))

            # Get scaling factors from config
            pan_scaling = self.pan_config.get('scaling_factor', 0.9) # Scaling factor for pan is for fine tuning the pan movement
            tilt_scaling = self.tilt_config.get('scaling_factor', 0.9) # Scaling factor for tilt is for fine tuning the tilt movement
            
            # Calculate final angles with scaling (multiplied by fov is to map the deviation to the actual angle, fov is the field of view of the camera)
            pan_angle = -x_deviation * self.fov['horizontal'] * pan_scaling # Negative sign for pan is because the servo is oriented in the opposite direction as the camera
            tilt_angle = y_deviation * self.fov['vertical'] * tilt_scaling # Positive sign for tilt is because the servo is oriented in the same direction as the camera
            
            return pan_angle, tilt_angle

    
    def should_update(self, pan_angle: float, tilt_angle: float) -> bool:
        """
        Determine if servo position should be updated based on angle changes.
        
        Args:
            pan_angle (float): Target pan angle
            tilt_angle (float): Target tilt angle
            
        Returns:
            bool: True if servos should be updated
        """
        delta_pan = abs(pan_angle - self.current_pan)
        delta_tilt = abs(tilt_angle - self.current_tilt)
        
        return (delta_pan >= self.pan_config['threshold'] or 
                delta_tilt >= self.tilt_config['threshold'])

    def update_if_needed(self, center_x: float, center_y: float) -> bool:
        """
        Calculate angles and update servo position if needed.
        
        Args:
            center_x (float): Normalized x coordinate (0-1)
            center_y (float): Normalized y coordinate (0-1)
            
        Returns:
            bool: True if servos were updated
        """
        pan_angle, tilt_angle = self.calculate_angles(center_x, center_y)
        if self.should_update(pan_angle, tilt_angle):
            self.move(pan_angle, tilt_angle)
            return True
        return False
    
    def cleanup(self):
        """Clean up hardware resources."""
        try:
            self.center()  # Return to center position
            self.pca.deinit() # Deinitialize PCA9685 (clean up resources)
            logging.info("Pan/Tilt controller cleaned up")
        except Exception as e:
            logging.error(f"Error during pan/tilt cleanup: {e}")