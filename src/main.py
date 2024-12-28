# src/main.py

from .hailo_detection_app import PersonDetectionApp

def main():
    try:
        app = PersonDetectionApp()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
