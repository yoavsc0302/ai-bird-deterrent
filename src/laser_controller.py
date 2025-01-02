import gpiod
import logging

class LaserController:
    def __init__(self, config: dict):
        """
        Initialize the laser controller.
        
        Args:
            config (dict): Configuration dictionary containing laser settings:
                - gpio_chip (str): The GPIO chip name (e.g., "gpiochip0")
                - pin (int): The GPIO pin number for the laser
        """
        try:
            # Extract configuration
            self.gpio_chip = config['gpio_chip']
            self.pin = config['pin']
            
            self.chip = None
            self.line = None
            
            # Setup GPIO
            self._setup_gpio()
            
            logging.info(f"Laser controller initialized on {self.gpio_chip} pin {self.pin}")
            
        except KeyError as e:
            logging.error(f"Missing configuration for laser: {e}")
            raise
        except Exception as e:
            logging.error(f"Failed to initialize laser controller: {e}")
            raise

    def _setup_gpio(self):
        """
        Set up the GPIO connection for the laser.
        
        Raises:
            Exception: If GPIO setup fails
        """
        try:
            self.chip = gpiod.Chip(self.gpio_chip) # Open GPIO chip for laser control
            self.line = self.chip.get_line(self.pin) # Get GPIO line for laser control (line is a GPIO pin)
            self.line.request(consumer="laser_control", type=gpiod.LINE_REQ_DIR_OUT) # Request control of the line (set as output)
            self.turn_off()  # Ensure laser starts in OFF state
            logging.info(f"Laser GPIO setup complete on {self.gpio_chip} pin {self.pin}")
        except Exception as e:
            logging.error(f"Failed to setup laser GPIO: {e}")
            raise

    def turn_on(self):
        """
        Turn the laser on.
        """
        try:
            if self.line:
                self.line.set_value(1) # Set GPIO pin to HIGH (3.3V)
                logging.debug("Laser turned ON")
        except Exception as e:
            logging.error(f"Failed to turn laser on: {e}")
            raise

    def turn_off(self):
        """
        Turn the laser off.
        """
        try:
            if self.line:
                self.line.set_value(0) # Set GPIO pin to LOW (0V)
                logging.debug("Laser turned OFF")
        except Exception as e:
            logging.error(f"Failed to turn laser off: {e}")
            raise

    def cleanup(self):
        """
        Clean up GPIO resources.
        Should be called before program exit.
        """
        try:
            if self.line: # Check if GPIO line is initialized
                self.turn_off()  # Ensure laser is off
                self.line.release() # Release control of the GPIO line (pin)
                logging.info("Laser GPIO resources cleaned up")
        except Exception as e:
            logging.error(f"Error during laser cleanup: {e}")