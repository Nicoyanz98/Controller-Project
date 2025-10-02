from inputs import devices, get_gamepad

INPUT_MAP = {
    "BTN_SOUTH": "A",
    "BTN_EAST": "B",
    "BTN_NORTH": "Y",
    "BTN_WEST": "X",
    "BTN_TL": "LB",
    "BTN_TR": "RB",
    "ABS_Z": "LT",
    "ABS_RZ": "RT",
    "ABS_X": "LSX",
    "ABS_Y": "LSY",
    "ABS_RX": "RSX",
    "ABS_RY": "RSY",
    "ABS_HAT0X": "DPadX",
    "ABS_HAT0Y": "DPadY",
    "BTN_START": "Start",
    "BTN_SELECT": "Select",
    "BTN_MODE": "Home"
}

TRIGGER_THRESHOLD = 70
STICK_THRESHOLD = 8000

def threshold_detection(btn_name, state):
    detected = False

    detected |= btn_name.startswith("R") and int(state) > TRIGGER_THRESHOLD # Triggers

    detected |= btn_name.startswith("Dpad") and int(state) == 1 # Dpad            
    
    if "S" in btn_name and abs(int(state)) > STICK_THRESHOLD:
        detected = True
        direction = btn_name[-1]
        btn_name = btn_name[:1]
        if int(state) > 0: 
            if direction == "X": btn_name += "Right"
            else: btn_name += "Up"
        else: 
            if direction == "X": btn_name += "Left"
            else: btn_name += "Down"

    if detected:
        return btn_name
    else:
        return None

def init_controller():
    if not devices.gamepads:
       print("No gamepad detected")
       exit(1)
    print(f"Gamepad detected: {devices.gamepads}")

def get_input():
    cur_pressed = set()

    while True:
        events = get_gamepad()
        for event in events:
            code = event.code
            state = event.state

            if code == "SYN_REPORT":
                continue

            btn_name = INPUT_MAP.get(code, f"Unknown({code})")

            if code.startswith("BTN_"):
                if state:  # pressed
                    cur_pressed.add(btn_name)
                else:  # released
                    cur_pressed.discard(btn_name)

            elif code.startswith("ABS_"):
                btn_name = threshold_detection(btn_name, state)
                if btn_name:
                    cur_pressed.add(btn_name)
        
            return cur_pressed
