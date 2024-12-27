# Import required GStreamer libraries
import gi
gi.require_version('Gst', '1.0')  # Ensure we're using GStreamer version 1.0
from gi.repository import Gst, GLib  # Main GStreamer and GLib libraries

# Standard Python imports
import os
import hailo  # Hailo AI accelerator library
import argparse

# Import necessary components from our common utilities
from hailo_rpi_common import (
    GStreamerApp,        # Base application class
    SOURCE_PIPELINE,     # Handles video input (camera/file)
    INFERENCE_PIPELINE,  # Handles AI model inference
    USER_CALLBACK_PIPELINE,  # Allows processing of detection results
    DISPLAY_PIPELINE,    # Handles video display
    app_callback_class,  # Base class for callback functionality
)

class SimpleDetectionApp(GStreamerApp):
    """
    Main application class for running object detection using Hailo AI accelerator.
    Inherits from GStreamerApp to handle pipeline management and basic functionality.
    """
    def __init__(self):
        """
        Initialize the detection application.
        Sets up paths, verifies files, and creates the GStreamer pipeline.
        """
        # Initialize GStreamer framework
        Gst.init(None)
        
        # Setup paths to required files
        # Get the absolute path to the project root directory
        current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Path to the YOLO model file (.hef format for Hailo)
        hef_path = os.path.join(current_path, 'resources', 'yolov8s_h8l.hef')
        # Path to the post-processing library (handles detection results)
        post_process_so = os.path.join(current_path, 'resources', 'libyolo_hailortpp_postprocess.so')
        
        # Verify that required files exist before proceeding
        if not os.path.exists(hef_path):
            raise FileNotFoundError(f"HEF file not found: {hef_path}")
        if not os.path.exists(post_process_so):
            raise FileNotFoundError(f"Post-process SO not found: {post_process_so}")
            
        # Create configuration arguments for the parent class
        args = argparse.Namespace(
            input="rpi",          # Use Raspberry Pi camera as input
            use_frame=False,      # Don't process frames in callback
            show_fps=True,        # Display FPS counter
            arch="hailo8l",       # Using Hailo 8L architecture
            hef_path=hef_path,    # Path to the AI model
            disable_sync=True,    # Run as fast as possible without frame sync
            dump_dot=False        # Don't create pipeline diagram
        )
        
        # Initialize the parent class with our configuration
        super().__init__(args, app_callback_class())
        
        # Store the paths as instance variables AFTER parent initialization
        # (parent init might override these values if set earlier)
        self.hef_path = hef_path
        self.post_process_so = post_process_so
        
        # Set up detection callback and create the pipeline
        self.app_callback = detection_callback
        self.create_pipeline()

    def get_pipeline_string(self):
        """
        Create the complete GStreamer pipeline string.
        This defines how video flows from input through AI processing to display.
        
        Returns:
            str: The complete GStreamer pipeline configuration
        """
        # Define parameters for the neural network inference
        inference_params = (
            "nms-score-threshold=0.3 "    # Minimum confidence for detections
            "nms-iou-threshold=0.45 "     # Intersection over Union threshold
            "output-format-type=HAILO_FORMAT_TYPE_FLOAT32"  # Output format
        )
        
        # Build the complete pipeline string:
        # 1. SOURCE_PIPELINE: Gets video from the RPi camera
        # 2. INFERENCE_PIPELINE: Runs the AI model on the video frames
        # 3. USER_CALLBACK_PIPELINE: Processes the detection results
        # 4. DISPLAY_PIPELINE: Shows the video with detection results
        pipeline = (
            f"{SOURCE_PIPELINE('rpi')} "  # Camera input
            f"{INFERENCE_PIPELINE(self.hef_path, self.post_process_so, batch_size=1, additional_params=inference_params)} ! "
            f"{USER_CALLBACK_PIPELINE()} ! "  # Process detections
            f"{DISPLAY_PIPELINE(video_sink='xvimagesink', sync='false', show_fps='true')}"  # Display output
        )
        
        # Print debug information
        print(f"\nUsing HEF path: {self.hef_path}")
        print(f"Pipeline: {pipeline}")
        return pipeline

def detection_callback(pad, info, user_data):
    """
    Callback function that processes each frame's detection results.
    
    Args:
        pad: GStreamer pad that triggered the callback
        info: Contains the GStreamer buffer with detection results
        user_data: Additional data passed to the callback
    
    Returns:
        Gst.PadProbeReturn.OK: Signals successful processing
    """
    # Get the buffer containing detection results
    buffer = info.get_buffer()
    if buffer:
        # Extract detections from the buffer
        detections = hailo.get_roi_from_buffer(buffer).get_objects_typed(hailo.HAILO_DETECTION)
        # Process each detected object
        for det in detections:
            print(f"Detected {det.get_label()} with confidence {det.get_confidence():.2f}")
    return Gst.PadProbeReturn.OK

def main():
    """
    Main entry point of the application.
    Creates and runs the detection application with error handling.
    """
    try:
        app = SimpleDetectionApp()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Standard Python idiom for running the main function
if __name__ == "__main__":
    main()