# src/hailo_detection_app.py

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import argparse
import os
import hailo
import numpy as np
import logging
import traceback
import gpiod  # Replace RPi.GPIO with gpiod

# Import from our local package
from .servo_control import PanTiltController
from .person_tracker import PersonTracker
from .hailo_rpi_common import (
    GStreamerApp,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
    app_callback_class,
)

class PersonDetectionApp(GStreamerApp):
    def __init__(self):
        Gst.init(None)

        # Paths to resources
        current_dir = os.path.dirname(os.path.abspath(__file__))  # src/
        project_dir = os.path.dirname(current_dir)                # ai-bird-deterrent/
        resources_dir = os.path.join(project_dir, 'resources')    # ai-bird-deterrent/resources/

        hef_path = os.path.join(resources_dir, 'yolov8s_h8l.hef')
        post_process_so = os.path.join(resources_dir, 'libyolo_hailortpp_postprocess.so')

        if not os.path.exists(hef_path):
            raise FileNotFoundError(f"HEF file not found: {hef_path}")
        if not os.path.exists(post_process_so):
            raise FileNotFoundError(f"Post-process SO not found: {post_process_so}")

        args = argparse.Namespace(
            input="rpi",
            use_frame=False,
            show_fps=True,
            arch="hailo8l",
            hef_path=hef_path,
            disable_sync=True,
            dump_dot=False
        )

        super().__init__(args, app_callback_class())

        self.hef_path = hef_path
        self.post_process_so = post_process_so

        # Initialize tracker + servo
        print("Initializing person tracker...")
        self.tracker = PersonTracker()

        print("Initializing pan/tilt servos...")
        self.pan_tilt = PanTiltController()

        # Setup laser using gpiod
        print("Initializing laser...")
        self.LASER_PIN = 13
        self.GPIO_CHIP = "gpiochip0"
        print(f"LASER_PIN set to {self.LASER_PIN}")
        try:
            # Initialize gpiod chip and line
            self.chip = gpiod.Chip(self.GPIO_CHIP)
            self.laser_line = self.chip.get_line(self.LASER_PIN)
            # Request the line as output
            self.laser_line.request(consumer="person_detection", type=gpiod.LINE_REQ_DIR_OUT)
            # Ensure laser starts OFF
            self.laser_line.set_value(0)
            print("GPIO setup for laser complete.")
        except Exception as e:
            print(f"Error during GPIO setup: {e}")
            print("Try running the script with appropriate permissions.")

        # Setup detection callback
        self.app_callback = self.detection_callback

        # Create the pipeline
        self.create_pipeline()

    def get_pipeline_string(self):
        # Additional hailonet params
        inference_params = (
            "nms-score-threshold=0.3 "
            "nms-iou-threshold=0.45 "
            "output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Build pipeline
        pipeline = (
            f"{SOURCE_PIPELINE('rpi')} "
            f"{INFERENCE_PIPELINE(self.hef_path, self.post_process_so, batch_size=1, additional_params=inference_params)} ! "
            f"{USER_CALLBACK_PIPELINE()} ! "
            f"{DISPLAY_PIPELINE(video_sink='xvimagesink', sync='false', show_fps='true')}"
        )
        return pipeline

    def detection_callback(self, pad, info, user_data):
        try:
            buffer = info.get_buffer()
            if not buffer:
                logging.warning("No buffer received.")
                return Gst.PadProbeReturn.OK

            # Retrieve caps from pad
            caps = pad.get_current_caps()
            if not caps:
                logging.warning("No caps available.")
                return Gst.PadProbeReturn.OK

            structure = caps.get_structure(0)
            frame_w = structure.get_value('width')
            frame_h = structure.get_value('height')

            rois = hailo.get_roi_from_buffer(buffer)
            all_detections = rois.get_objects_typed(hailo.HAILO_DETECTION)

            if not all_detections:
                logging.info("No detections found.")
                self.laser_line.set_value(0)  # Turn laser off using gpiod
                return Gst.PadProbeReturn.OK

            # Filter only 'person' detections
            person_detections = []
            for det in all_detections:
                label = det.get_label()
                if label == "person":
                    person_detections.append(det)
                else:
                    rois.remove_object(det)

            if not person_detections:
                logging.info("No person detections after filtering.")
                self.laser_line.set_value(0)  # Turn laser off using gpiod
                return Gst.PadProbeReturn.OK

            # If we found a person, turn on laser
            try:
                # Turn laser on using gpiod
                self.laser_line.set_value(1)
                print("Laser turned ON.")

            except Exception as e:
                logging.error(f"Error controlling laser: {e}")
                traceback.print_exc()

            # Rest of the detection callback remains the same...
            self.tracker.update(person_detections)

            # Find the largest detection
            largest_det = None
            largest_area = 0.0
            for det in person_detections:
                bbox = det.get_bbox()
                w, h = bbox.width(), bbox.height()
                area = w * h
                if area > largest_area:
                    largest_area = area
                    largest_det = det

            # Move servo if found one
            if largest_det:
                bbox = largest_det.get_bbox()
                x_min, y_min = bbox.xmin(), bbox.ymin()
                x_max, y_max = bbox.xmax(), bbox.ymax()

                center_x = (x_min + x_max) / 2.0
                center_y = (y_min + y_max) / 2.0
                logging.info(f"Largest person center: ({center_x:.2f}, {center_y:.2f})")

                # Calculate angles using FOV-aware mapping
                H_FOV = 63.0  # Raspberry Pi Camera Module 3 horizontal FOV
                V_FOV = 48.8  # Raspberry Pi Camera Module 3 vertical FOV

                # Convert normalized coordinates [-0.5, 0.5] to angles
                normalized_x = center_x - 0.5
                normalized_y = center_y - 0.5

                # Apply tangent-based mapping for more accurate angle calculation
                raw_pan_angle = -normalized_x * H_FOV
                raw_tilt_angle = normalized_y * V_FOV

                # Apply smoothing factor to reduce overshooting
                SMOOTHING = 0.5  # More aggressive smoothing to reduce overshooting
                pan_angle = raw_pan_angle * SMOOTHING
                tilt_angle = raw_tilt_angle * SMOOTHING

                logging.info(f"Calculated angles - Pan: {pan_angle:.2f}°, Tilt: {tilt_angle:.2f}°")

                # Define a threshold for movement to prevent jitter
                PAN_THRESHOLD = 5.0  # degrees
                TILT_THRESHOLD = 5.0  # degrees

                # Calculate differences
                delta_pan = pan_angle - self.pan_tilt.current_pan
                delta_tilt = tilt_angle - self.pan_tilt.current_tilt

                if abs(delta_pan) >= PAN_THRESHOLD or abs(delta_tilt) >= TILT_THRESHOLD:
                    self.pan_tilt.move(pan_angle, tilt_angle)
                else:
                    logging.info("Change in angles below threshold; not moving servos.")

            return Gst.PadProbeReturn.OK

        except Exception as e:
            logging.error(f"Error in detection callback: {e}")
            traceback.print_exc()
            return Gst.PadProbeReturn.OK

    def cleanup(self):
        print("Cleaning up... Deinitializing servo and laser.")
        try:
            self.laser_line.set_value(0)  # Ensure laser is OFF
            self.laser_line.release()  # Release the GPIO line
            print("Laser cleanup complete.")
        except Exception as e:
            print(f"Error during laser cleanup: {e}")
        self.pan_tilt.cleanup()