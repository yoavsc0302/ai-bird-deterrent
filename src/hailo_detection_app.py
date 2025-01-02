"""
Main Person Detection Application

This module implements the core person detection and tracking functionality using
Hailo's ML acceleration and hardware control for the bird deterrent system.
"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import os
import hailo
import logging
import traceback
from typing import Optional, Tuple

from .config import load_config
from .servo_control import PanTiltController
from .laser_control import LaserController
from .hailo_rpi_common import (
    GStreamerApp,
    SOURCE_PIPELINE, # Gets frames (video) from Raspberry Pi camera
    INFERENCE_PIPELINE, # Runs MLmodel inference on frames using Hailo
    TRACKER_PIPELINE, # 
    USER_CALLBACK_PIPELINE, # Where we process the inference results
    DISPLAY_PIPELINE, # Displays the video with bounding boxes
    app_callback_class,
)

class PersonDetectionApp(GStreamerApp):
    """
    Main application class for person detection and tracking.
    
    This class integrates:
    - Video capture and ML inference using Hailo
    - Person tracking
    - Servo control for pan/tilt
    - Laser control
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the person detection application.
        
        Args:
            config_path (str): Path to the YAML configuration file
        """

        # 1. Load configuration & setup logs
        self.config = load_config(config_path)
        self._setup_logging()

        # 2. Setup args for parent class
        args = self._create_gstreamer_args()
        super().__init__(args, app_callback_class())

        # 3. Initialize hardware components
        self._init_hardware()

        # 4. Setup detection callback (which is called for each frame)
        self.app_callback = self._detection_callback

        # 5. Create the GStreamer pipeline
        self.create_pipeline() # uses get_pipeline_string() which we created here below, to create the pipeline
        
        # 6. Initialize the ID of the person being tracked
        self.tracked_id = None 
    
    def _setup_logging(self):
        """Configure logging for the application.
            1. Creates logs directory if it doesn't exist
            2. Sets up logging into 'hailort.log'
        """
        logs_dir = self.config['paths'].get('logs_dir', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        logging.basicConfig(
            filename=os.path.join(logs_dir, 'hailort.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _create_gstreamer_args(self):
        """Create arguments for GStreamer initialization."""
        from argparse import Namespace
        return Namespace(
            input="rpi", # we are using raspbery pi camera
            use_frame=False,
            show_fps=True,
            arch="hailo8l", # we are using hailo8l chip (not hailo8)
            hef_path=self.config['paths']['model']['hef_path'], # our hef model suited for hailo8l chip
            disable_sync=True,
            dump_dot=False
        )
    
    def _init_hardware(self):
        try:
            logging.info("Initializing hardware components...")

            # Initialize pan/tilt servos
            logging.info("Initializing pan/tilt servos...")
            self.pan_tilt = PanTiltController(config=self.config)

            # Initialize laser
            logging.info("Initializing laser...")
            self.laser = LaserController(config=self.config['laser'])

            logging.info("All hardware components initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize hardware: {e}")
            self.cleanup()
            raise
    
    def _detection_callback(self, pad, info, user_data) -> Gst.PadProbeReturn:
        """Process detection results and control hardware.
        
            info - is a GStreamer probe info object that contains:
            - The current buffer (frame) being processed
            - more information about the buffer

            buffer - is the frame itself, but also contains:
            - The image data
            - The ML model inference results
            - The bounding boxes around detected objects
            - The labels of the detected objects
            - The confidence scores of the detected objects
            - And more
            """

        try:    
            # Get buffer (frame) from probe info
            buffer = info.get_buffer()
            if not buffer: 
                logging.warning("No buffer received in detection callback")
                return Gst.PadProbeReturn.OK
            
            # Get detections
            rois = hailo.get_roi_from_buffer(buffer)
            all_detections = rois.get_objects_typed(hailo.HAILO_DETECTION)

            # Filter for high-confidence person detections and remove non-person detections from ROIs
            person_detections = []
            for det in all_detections:
                if det.get_label() == "person" and det.get_confidence() >= self.config['detection']['nms_score_threshold']:
                    tracking_ids = det.get_objects_typed(hailo.HAILO_UNIQUE_ID)
                    if tracking_ids:
                        person_detections.append(det)
                else:
                    rois.remove_object(det)  # Remove all objects initially

            # If no people detected, turn off laser
            if not person_detections:
                self.laser.turn_off()
                return Gst.PadProbeReturn.OK

            # Get person with lowest tracking ID
            selected_person = min(person_detections, key=lambda x: x.get_objects_typed(hailo.HAILO_UNIQUE_ID)[0].get_id())
                
            # Calculate target position, turn on laser, and update pan/tilt
            center_x, center_y = self.target_position(selected_person)
            self.laser.turn_on()
            self.pan_tilt.update_if_needed(center_x, center_y)

            return Gst.PadProbeReturn.OK

        except Exception as e:
            logging.error(f"Error in detection callback: {e}")
            traceback.print_exc()
            return Gst.PadProbeReturn.OK
    
    def get_pipeline_string(self) -> str:
        """Create the GStreamer pipeline string."""
        # Configure inference parameters
        inference_params = (
            f"nms-score-threshold={self.config['detection']['nms_score_threshold']} "
            f"nms-iou-threshold={self.config['detection']['nms_iou_threshold']} "
            "output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )
        
        # Build pipeline
        pipeline = (
            f"{SOURCE_PIPELINE('rpi')} "
            f"{INFERENCE_PIPELINE(self.config['paths']['model']['hef_path'], self.config['paths']['model']['post_process_path'], batch_size=1, additional_params=inference_params)} ! "
            f"{TRACKER_PIPELINE()} ! "
            f"{USER_CALLBACK_PIPELINE()} ! "
            f"{DISPLAY_PIPELINE(video_sink='xvimagesink', sync='false', show_fps='true')}"
        )
        return pipeline
    
    def cleanup(self):
        """Clean up hardware resources."""
        logging.info("Cleaning up hardware resources...")
        try:
            self.laser.cleanup()
            self.pan_tilt.cleanup()
            logging.info("Hardware cleanup completed successfully")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def target_position(self, selected_person):
        """Calculate target position for the selected person."""
        bbox = selected_person.get_bbox()
        center_x = (bbox.xmin() + bbox.xmax()) / 2.0
        center_y = (bbox.ymin() + bbox.ymax()) / 2.0
        return center_x, center_y