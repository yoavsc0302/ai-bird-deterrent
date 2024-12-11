from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort

# Load YOLOv8 model
model = YOLO("./models/yolov8n.pt")

# Initialize DeepSORT tracker
tracker = DeepSort(max_age=30)

# Initialize picamera2
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(camera_config)
picam2.start()

try:
    while True:
        # Capture a frame
        frame = picam2.capture_array()

        # Run YOLO detection
        results = model.predict(source=frame, conf=0.5, save=False, save_txt=False)
        detections = results[0].boxes.data.cpu().numpy() if results[0].boxes else []

        # Extract detections for people only
        detection_list = []
        for detection in detections:
            x1, y1, x2, y2, conf, class_id = detection
            if int(class_id) == 0:  # 0 = 'person' in COCO labels
                # Convert to [x, y, w, h] format
                w = int(x2 - x1)
                h = int(y2 - y1)
                detection_list.append(([int(x1), int(y1), w, h], conf))
        
        print("Detections:", detection_list)

        # Track detections with DeepSORT
        tracks = tracker.update_tracks(detection_list, frame=frame)

        # Draw tracking results
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            bbox = track.to_ltrb()
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the frame
        cv2.imshow("YOLOv8 + DeepSORT Tracking", frame)

        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()