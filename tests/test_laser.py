import gpiod
import time


# Configuration
GPIO_CHIP = "/dev/gpiochip0"  # The GPIO chip (use gpiodetect to confirm)
LASER_PIN = 13  # GPIO pin connected to the signal (S)


print(f"Using GPIO chip: {GPIO_CHIP}")
chip = gpiod.Chip(GPIO_CHIP)


# Initialize the GPIO chip and line
chip = gpiod.Chip(GPIO_CHIP)
line = chip.get_line(LASER_PIN)

# Request the line as output
line.request(consumer="laser_test", type=gpiod.LINE_REQ_DIR_OUT)

print("Starting laser test...")

# Blink the laser 5 times
for i in range(5):
    print(f"Laser ON (Blink {i + 1}/5)")
    line.set_value(1)  # Turn the laser ON
    time.sleep(1)  # Keep it ON for 1 second
    
    print(f"Laser OFF (Blink {i + 1}/5)")
    line.set_value(0)  # Turn the laser OFF
    time.sleep(1)  # Keep it OFF for 1 second

print("Laser test completed.")
line.set_value(0)  # Ensure the laser is OFF
