from utils import BoxesMutex, HandDataMutex
from hand.hand_inferencer import HandInferencer
from joystick.joystick_boxes_inferencer import JoystickBoxesInferencer
from input_detector import JoystickInputDetector

import argparse

import faulthandler
faulthandler.enable()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Joystick Input Detector")
    parser.add_argument('--hand_model', type=str, default='./hand/hand_landmarker.task', help='Path to the hand landmarker model')
    parser.add_argument('--joystick_model', type=str, default='./joystick/joystick_yolo_v2.pt', help='Path to the joystick YOLO model')
    args = parser.parse_args()

    hand_detection_mutex = HandDataMutex()
    boxes_mutex = BoxesMutex()
    joystick_boxes_inferencer = JoystickBoxesInferencer(boxes_mutex, model_path=args.joystick_model)
    hand_inferencer = HandInferencer(hand_detection_mutex, model_path=args.hand_model)
    input_detector = JoystickInputDetector(hand_detection_mutex, boxes_mutex, hand_inferencer, joystick_boxes_inferencer)

    input_detector.start()
