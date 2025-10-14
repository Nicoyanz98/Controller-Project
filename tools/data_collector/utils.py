import os
import pickle
import cv2
from .config import COUNTER_FILE, SAVE_FOLDER
from .samples import generate_samples

def load_progress():
    with open(COUNTER_FILE, 'rb') as f:
        counters = pickle.load(f)
    print(f"Loaded counters.")
    return counters


def get_counters(combinations):
    if os.path.exists(COUNTER_FILE):
        choice = input(f"Saved session found. Continue? (y/n): ").lower()
        if choice == 'y':
            return load_progress()
        
    trial = input("Write new trial number to avoid overwritting existing examples: ")

    counters = {}
    for b in combinations:
        key = "+".join(b)
        counters[key] = 0

    return counters, trial

def save_progress(counters):
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


def save_image(label_text, counters, frame, trial):
    filename = os.path.join(f"{SAVE_FOLDER}/{trial}", f"{label_text}_{counters[label_text]}.png")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    cv2.imwrite(filename, frame)
    print(f"Saved {filename}")

def wait_for_key(delay=1):
    return chr(cv2.waitKey(delay) & 0xFF).lower()


def handle_keypress(key, cap, counters=None, save_fn=None):
    if key == 'q':
        close_camera(cap)
        return "quit"
    if key == 'p' and save_fn and counters:
        save_fn(counters)
        print("Progress saved. You can continue later.")
        close_camera(cap)
        return "pause"
    if key == ' ':
        return "start"
    return None

def close_camera(cap):
    cap.release()
    cv2.destroyAllWindows()
