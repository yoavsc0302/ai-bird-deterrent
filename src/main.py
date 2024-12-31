"""
Main entry point for the AI Bird Deterrent system.
"""

import sys
import signal
import logging
from pathlib import Path
import argparse

from .hailo_detection_app import PersonDetectionApp
from .config import ConfigurationError

def parse_args():
    """
    Parse command line arguments.

    This function sets up and processes command-line arguments for the application.
    Currently supports specifying a custom configuration file path.

    Returns:
        argparse.Namespace: Parsed arguments containing:
            - config (str): Path to configuration file

    Examples:
        Default usage:
            $ python -m src.main
            # Uses default 'config.yaml'

        Custom config:
            $ python -m src.main --config custom_config.yaml
            # Uses 'custom_config.yaml'
    """
    parser = argparse.ArgumentParser(description='AI Bird Deterrent System')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    return parser.parse_args()

def setup_signal_handlers(app):
    """Setup signal handlers for graceful shutdown.

    # When user runs program:
    python -m src.main

    # Program is running...
    # User presses Ctrl+C
    # What happens:
    1. SIGINT signal is sent
    2. Our signal_handler catches it
    3. Logs "Received signal 2" (SIGINT is signal 2)
    4. Calls app.cleanup() which:
    - Turns off laser
    - Centers servos
    - Releases hardware resources
    5. Exits program cleanly

    Without this handler:
     - Laser might stay up
     - Resources might not be released causing unpredictable behavior
    """
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}")
        app.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler) # When SIGINT occurs, run signal_handler
    signal.signal(signal.SIGTERM, signal_handler) # Wehn SIGTERM occurs, run signal_handler

def main():
    """Main entry point of the application."""
    args = parse_args()
    
    try:
        # Ensure config file exists
        config_path = Path(args.config) # Path to configuration file, which
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        # Initialize and run the application
        app = PersonDetectionApp(config_path=str(config_path))
        setup_signal_handlers(app)
        
        logging.info("Starting AI Bird Deterrent system...")
        app.run()
        
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()