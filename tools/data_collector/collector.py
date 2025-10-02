import cv2, time, os
from .config import SAVE_FOLDER, COUNTDOWN_TIME, RESET_PAUSE, TRIAL
from .utils import get_remaining_samples, save_progress, close_camera, show_frame_with_text, wait_for_key, handle_keypress
from .controller import init_controller, get_input

# TODO: Save frame is repeated code
# TODO: TESTING LAST COMMIT

def input_collector(cam):
    init_controller()

    counters = {}

    def show_video(): 
        if not show_frame_with_text(cam, "", color=(0, 0, 0)):
            print("Error showing")
            exit(1)

    def save_frame(label_text):
        ret, frame = cam.read()
        if ret:
            filename = os.path.join(f"{SAVE_FOLDER}/{TRIAL}", f"{label_text}_{counters[label_text]}.png")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
            counters[label_text] += 1

    # TODO: Set condition for stopping, for now its only until I press 'q'
    while True: 
        get_input(waiting_fn=show_video, action_fn=save_frame)

def timed_collector(cam):
    # TODO: Delete progress by skipping saved progress
    remaining, counters = get_remaining_samples()

    # While there are stil remaining examples to add
    while remaining:
        combo = remaining[0]
        label_text = "+".join(combo)
        if label_text not in counters:
            counters[label_text] = 1

        print(f"Get ready to press: {label_text}")

        for i in range(COUNTDOWN_TIME*10, 0, -1):
            if not show_frame_with_text(cam, f"Capturing {label_text} in {i//10}...", color=(0, 0, 255)):
                break
            
            key = wait_for_key(100)
            action = handle_keypress(key, cam, remaining, counters, save_progress)
            
            if action in ["quit", "pause"]:
                close_camera(cam)
                return

        ret, frame = cam.read()
        if ret:
            filename = os.path.join(f"{SAVE_FOLDER}/{TRIAL}", f"{label_text}_{counters[label_text]}.png")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
            counters[label_text] += 1
        
        remaining.remove(combo)

        time.sleep(RESET_PAUSE)

def run_collector(connected):
    # Opening camera
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Setup: Adjust your position in front of the camera.")
    print("Press SPACE to start collecting data, or 'q' to quit.")

    # Camera preview loop
    while True:
        if not show_frame_with_text(cam, "Adjust camera. Press SPACE to start."):
            continue
        
        key = wait_for_key()
        action = handle_keypress(key, cam)
        
        if action == "quit":
            return
        if action == "start":
            print("Starting...")
            break
    
    print("Press 'q' to quit, 'p' to pause and save progress.")

    if connected:
        input_collector(cam)
    else:
        timed_collector(cam)
    
    # TODO: Delete progress after completing

    print("Dataset collection complete")
    close_camera(cam)
