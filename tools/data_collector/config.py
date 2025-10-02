import os

# Folder to save dataset images
SAVE_FOLDER = "./dataset"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# File names for saving state
SAVE_STATE_FILE = os.path.join(SAVE_FOLDER, "state/remaining_samples.pkl")
COUNTER_FILE = os.path.join(SAVE_FOLDER, "state/counters.pkl")

# PARAMETERS (time measured in seconds)
MIN_SAMPLES_PER_BUTTON = 10
MIN_SAMPLES_PER_COMBO = int(.5 * MIN_SAMPLES_PER_BUTTON)
COUNTDOWN_TIME = 6
RESET_PAUSE = 1

# Types of buttons
face_buttons = ["A", "B", "X", "Y"]
dpad = ["Dpad_Up", "Dpad_Down", "Dpad_Left", "Dpad_Right"]
ls = ["LS_Up", "LS_Down", "LS_Left", "LS_Right"]
rs = ["RS_Up", "RS_Down", "RS_Left", "RS_Right"]
bumpers = ["LB", "RB"]
triggers = ["LT", "RT"]
stick_buttons = ["L3", "R3"]
system = ["Start", "Select", "Home"]
idle = ["Idle"]

all_buttons = face_buttons + dpad + ls + rs + bumpers + triggers + stick_buttons + system

TRIAL = 0
