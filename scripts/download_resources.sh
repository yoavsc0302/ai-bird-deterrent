#!/bin/bash

# Define download function
download_model() {
  wget -nc "$1" -P ./resources
}

# YOLO8 models specifically compiled for HAILO8L
H8L_HEFS=(
  "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/yolov8s_h8l.hef"
  "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/yolov8s_pose_h8l.hef"
)

# Download HAILO8L models
echo "Downloading HAILO8L YOLO8 models..."
for url in "${H8L_HEFS[@]}"; do
  download_model "$url"
done