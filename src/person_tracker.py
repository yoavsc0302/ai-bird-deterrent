class PersonTracker:
    def __init__(self, max_frames_missing=10):
        self.tracked_objects = {}
        self.next_id = 1
        self.current_frame = 0
        self.max_frames_missing = max_frames_missing
        self.selected_id = None

    def _calculate_iou(self, box1, box2):
        bbox1 = box1.get_bbox()
        bbox2 = box2.get_bbox()
        
        x1_min, y1_min = bbox1.xmin(), bbox1.ymin()
        x1_max, y1_max = bbox1.xmax(), bbox1.ymax()
        x2_min, y2_min = bbox2.xmin(), bbox2.ymin()
        x2_max, y2_max = bbox2.xmax(), bbox2.ymax()

        x_min = max(x1_min, x2_min)
        y_min = max(y1_min, y2_min)
        x_max = min(x1_max, x2_max)
        y_max = min(y1_max, y2_max)

        if x_max < x_min or y_max < y_min:
            return 0.0

        intersection = (x_max - x_min) * (y_max - y_min)
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def update(self, detections):
        self.current_frame += 1
        matched_detections = set()
        matched_tracks = set()

        # Filter for person detections
        person_detections = [det for det in detections if det.get_label() == "person"]

        # Match existing tracks with new detections
        for track_id, track_info in self.tracked_objects.items():
            best_iou = 0.3
            best_detection = None

            for detection in person_detections:
                if detection in matched_detections:
                    continue

                iou = self._calculate_iou(track_info['detection'], detection)
                if iou > best_iou:
                    best_iou = iou
                    best_detection = detection

            if best_detection:
                self.tracked_objects[track_id]['detection'] = best_detection
                self.tracked_objects[track_id]['last_seen'] = self.current_frame
                matched_detections.add(best_detection)
                matched_tracks.add(track_id)
                print(f"Updated track {track_id}")

        # Create new tracks for unmatched person detections
        for detection in person_detections:
            if detection not in matched_detections:
                self.tracked_objects[self.next_id] = {
                    'detection': detection,
                    'last_seen': self.current_frame,
                    'id': self.next_id
                }
                if self.selected_id is None:
                    self.selected_id = self.next_id
                print(f"Created new track {self.next_id}")
                self.next_id += 1

        # Remove old tracks
        current_tracks = dict(self.tracked_objects)
        for track_id, track_info in current_tracks.items():
            if self.current_frame - track_info['last_seen'] > self.max_frames_missing:
                del self.tracked_objects[track_id]
                if track_id == self.selected_id:
                    self.selected_id = min(self.tracked_objects.keys()) if self.tracked_objects else None
                print(f"Removed track {track_id}")

        if self.selected_id:
            print(f"Following person with ID {self.selected_id}")

        return self.get_selected_detection()

    def get_selected_detection(self):
        if self.selected_id and self.selected_id in self.tracked_objects:
            return self.tracked_objects[self.selected_id]['detection']
        return None

    def get_tracked_detections(self):
        """Returns all currently tracked detections with their IDs"""
        return [(track_info['detection'], track_info['id']) 
                for track_info in self.tracked_objects.values()]