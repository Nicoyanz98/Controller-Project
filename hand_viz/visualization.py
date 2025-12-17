from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
import cv2
import threading
import time

from threads import CameraThread, DetectionThread, HandsThread

class JoystickDetector:
    def __init__(self):
        self.model = YOLO("models/best.pt")

        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path="models/hand_landmarker.task"),
            running_mode=vision.RunningMode.IMAGE,
            # min_hand_detection_confidence=0.5,
            # min_hand_presence_confidence=0.5,
            # min_tracking_confidence=0.5,
            num_hands=2
        )
        self.hand_recognizer = vision.HandLandmarker.create_from_options(options)


        self.running = True

        self.current_frame = None
        self.current_results = None
        self.hands_detection = None
        
        self.frame_lock = threading.Lock()
        self.results_lock = threading.Lock()
        self.hands_detection_lock = threading.Lock()

        self.target_fps = 30  
        self.frame_time = 1.0 / self.target_fps

        self.fps_count = 0
        self.fps = 0

        self.threads = {
            "camera": CameraThread(self), 
            "detection": DetectionThread(self),
            "hands": HandsThread(self)
        }
    
    def display_hand_landmarks(self, display_frame):
        MARGIN = 10  # pixels
        FONT_SIZE = 1
        FONT_THICKNESS = 1
        HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green

        with self.hands_detection_lock:
            hand_landmarks_list = self.hands_detection.hand_landmarks
            handedness_list = self.hands_detection.handedness

        # Loop through the detected hands to visualize.
        for idx in range(len(hand_landmarks_list)):
            hand_landmarks = hand_landmarks_list[idx]
            handedness = handedness_list[idx]

            # Draw the hand landmarks.
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
            ])
            mp.solutions.drawing_utils.draw_landmarks(
                display_frame,
                hand_landmarks_proto,
                mp.solutions.hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style()
            )

            # Get the top left corner of the detected hand's bounding box.
            height, width, _ = display_frame.shape
            x_coordinates = [landmark.x for landmark in hand_landmarks]
            y_coordinates = [landmark.y for landmark in hand_landmarks]
            text_x = int(min(x_coordinates) * width)
            text_y = int(min(y_coordinates) * height) - MARGIN

            # Draw handedness (left or right hand) on the image.
            cv2.putText(display_frame, f"{handedness[0].category_name}", (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA
            )

    def display_boxes(self, display_frame):
        with self.results_lock:
            current_results = self.current_results
        
        if (current_results is not None and current_results.boxes is not None and len(current_results.boxes) > 0):
            boxes = current_results.boxes.xyxy.cpu().numpy()
            classes = current_results.boxes.cls.cpu().numpy()
            confidences = current_results.boxes.conf.cpu().numpy()
            
            for _, (box, class_id, confidence) in enumerate(zip(boxes, classes, confidences)):
                x1, y1, x2, y2 = map(int, box)
                class_id = int(class_id)
                class_name = self.model.names[class_id]
                confidence = float(confidence)
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{class_name}: {confidence:.2f}"
                cv2.putText(display_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    def display_fps(self, display_frame, current_time):
        self.fps_count += 1 #Contamos los frames
        if current_time - self.fps_time >= 1.0: #Si paso mas de un segundo, actuazamos el contador
            self.fps = self.fps_count
            self.fps_count = 0
            self.fps_time = current_time
        
        cv2.putText(display_frame, f"FPS: {self.fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def run(self):
        #incializamos hilos
        cam_thread = threading.Thread(target=self.threads["camera"].run)
        det_thread = threading.Thread(target=self.threads["detection"].run)
        hand_thread = threading.Thread(target=self.threads["hands"].run)
        
        #Damos variable para que inice con el programa y cierre con el mismo
        cam_thread.daemon = True
        det_thread.daemon = True
        hand_thread.daemon = True
        cam_thread.start()
        det_thread.start()
        hand_thread.start()
        
        self.fps_time = time.time()
        last_display_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            if current_time - last_display_time >= self.frame_time:
                last_display_time = current_time

                #Dibujamos el frame acutal
                if self.current_frame is not None:
                    with self.frame_lock:
                        display_frame = self.current_frame.copy()
                    
                    # Boxes
                    self.display_boxes(display_frame)

                    self.display_hand_landmarks(display_frame)
                    
                    # FPS
                    self.display_fps(display_frame, current_time)

                    cv2.imshow("Detector de joystick", display_frame)

            time.sleep(0.001)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                self.running = False
                break
        
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = JoystickDetector()
    detector.run()