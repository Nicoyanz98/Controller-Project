import os
import pickle
import cv2
from .config import SAVE_STATE_FILE, COUNTER_FILE
from .samples import generate_samples

def load_progress():
    with open(SAVE_STATE_FILE, 'rb') as f:
        samples = pickle.load(f)
    with open(COUNTER_FILE, 'rb') as f:
        counters = pickle.load(f)
    print(f"Loaded {len(samples)} remaining samples.")
    return samples, counters


def get_remaining_samples():
    if os.path.exists(SAVE_STATE_FILE) and os.path.exists(COUNTER_FILE):
        choice = input(f"Saved session found. Continue? (y/n): ").lower()
        if choice == 'y':
            return load_progress()
        
    TRIAL = input("Write new trial number to avoid overwritting existing examples: ")
    return generate_samples(), {}

def save_progress(remaining, counters):
    os.makedirs(os.path.dirname(SAVE_STATE_FILE), exist_ok=True)
    with open(SAVE_STATE_FILE, 'wb') as f:
        pickle.dump(remaining, f)
    os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
    with open(COUNTER_FILE, 'wb') as f:
        pickle.dump(counters, f)

def show_frame_with_text(cap, text, color=(0, 255, 255)):
    ret, frame = cap.read()
    if not ret:
        return False
    cv2.putText(frame, text, (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
    cv2.imshow("Webcam", frame)
    return True


def wait_for_key(delay=1):
    return chr(cv2.waitKey(delay) & 0xFF).lower()


def handle_keypress(key, cap, remaining=None, counters=None, save_fn=None):
    if key == 'q':
        close_camera(cap)
        return "quit"
    if key == 'p' and save_fn and remaining and counters:
        save_fn(remaining, counters)
        print("Progress saved. You can continue later.")
        close_camera(cap)
        return "pause"
    if key == ' ':
        return "start"
    return None

def close_camera(cap):
    cap.release()
    cv2.destroyAllWindows()
