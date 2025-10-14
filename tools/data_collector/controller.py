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
    "ABS_X": "LS_X",
    "ABS_Y": "LS_Y",
    "ABS_RX": "RS_X",
    "ABS_RY": "RS_Y",
    "ABS_HAT0X": "Dpad_X",
    "ABS_HAT0Y": "Dpad_Y",
    "BTN_START": "Start",
    "BTN_SELECT": "Select",
    "BTN_MODE": "Home"
}

TRIGGER_THRESHOLD = 70
STICK_THRESHOLD = 15000

def threshold_detection(btn_name, state, last_pressed):
    detected = False

    detected |= btn_name.endswith("T") and int(state) > TRIGGER_THRESHOLD # Triggers

    if btn_name.startswith("Dpad"): # Dpad
        detected = abs(int(state)) == 1 
        direction = btn_name[-1]
        btn_name = btn_name[:5]
        if int(state) > 0: 
            if direction == "X": btn_name += "Right"
            else: btn_name += "Down"
        elif int(state) < 0: 
            if direction == "X": btn_name += "Left"
            else: btn_name += "Up"
        else:
            for btn in last_pressed:
                if "Dpad_" in btn:
                    btn_name = btn
    
    if "S" in btn_name:
        detected = abs(int(state)) > STICK_THRESHOLD
        direction = btn_name[-1]
        btn_name = btn_name[:3]
        if int(state) > 0: 
            if direction == "X": btn_name += "Right"
            else: btn_name += "Down"
        else: 
            if direction == "X": btn_name += "Left"
            else: btn_name += "Up"

    return btn_name, detected

def init_controller():
    if not devices.gamepads:
       print("No gamepad detected")
       exit(1)
    print(f"Gamepad detected: {devices.gamepads}")

def get_input(waiting_fn, action_fn):
    cur_pressed = set()
    last_pressed = set()

    while True:
        waiting_fn()
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
                btn_name, state = threshold_detection(btn_name, state, last_pressed)
                if state:
                    cur_pressed.add(btn_name)
                else:
                    cur_pressed.discard(btn_name)
        
            if len(cur_pressed) > 0:
                last_pressed = cur_pressed
                if ("Dpad_Down" in cur_pressed and "Dpad_Up" in cur_pressed) or ("Dpad_Left" in cur_pressed and "Dpad_Right" in cur_pressed):
                    cur_pressed = set()
                    continue
                print(cur_pressed)
                action_fn(cur_pressed)
