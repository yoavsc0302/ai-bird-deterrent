import gpiod

try:
    for i in range(0, 14):  # Adjust based on your GPIO range
        device_name = f"gpiochip{i}"
        try:
            chip = gpiod.Chip(device_name)
            print(f"Successfully accessed {device_name}: {chip.name()}")
        except FileNotFoundError:
            print(f"failed: {i}")
except Exception as e:
    print(f"GPIO access failed: {e}")
