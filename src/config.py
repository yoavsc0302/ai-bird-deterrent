"""
Configuration Module

This module handles loading and validating the application configuration from YAML.
"""

import os
import yaml
from typing import Dict, Any

class ConfigurationError(Exception):
    """Raised when there's an error in the configuration."""
    pass

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load and validate the configuration from a YAML file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        Dict[str, Any]: Loaded and validated configuration
        
    Raises:
        ConfigurationError: If configuration is invalid or missing required fields
    """
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse configuration file: {e}")
    
    # Validate and process paths
    resources_dir = config.get('paths', {}).get('resources_dir')
    if not resources_dir:
        raise ConfigurationError("resources_dir not specified in configuration")
    
    # Make paths absolute if they're relative
    if not os.path.isabs(resources_dir):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config['paths']['resources_dir'] = os.path.join(base_dir, resources_dir)
    
    # Validate required model files exist
    model_config = config.get('paths', {}).get('model', {})
    hef_path = os.path.join(config['paths']['resources_dir'], model_config.get('hef_file', ''))
    post_process_path = os.path.join(config['paths']['resources_dir'], model_config.get('post_process_so', ''))
    
    if not os.path.exists(hef_path):
        raise ConfigurationError(f"HEF file not found: {hef_path}")
    if not os.path.exists(post_process_path):
        raise ConfigurationError(f"Post-process SO file not found: {post_process_path}")
    
    # Add processed paths to config
    config['paths']['model']['hef_path'] = hef_path
    config['paths']['model']['post_process_path'] = post_process_path
    
    return config