import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

import cv2

import time, math

from handposeRecognizer import Handpose_Recognizer
from frameAnnotator import Frame_Annotator

gesture_recognizer = Handpose_Recognizer()
annotator = Frame_Annotator()

# Use OpenCV’s VideoCapture to start capturing from the webcam.
cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Error: Could not open webcam.")
    exit(1)

previous_time = 0
last_distance = None

# Create a loop to read the latest frame from the camera using VideoCapture#read()
while cam.isOpened():
    _, frame = cam.read()
    frame = cv2.flip(frame, 1)
    if cv2.waitKey(1) == ord('q'):
        break

    annotator.update_frame(frame)

    # Convert the frame received from OpenCV to a MediaPipe’s Image object.
    gesture_recognizer.recognize_async(frame)
    annotator.draw_keypoints_on_image(gesture_recognizer.result)

    last_distance = annotator.show_distance(last_distance)

    cv2.imshow("Webcam", annotator.annotated_frame)

gesture_recognizer.close()
cam.release()
cv2.destroyAllWindows()