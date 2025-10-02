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

def init_controller():
    if not devices.gamepads:
       print("No gamepad detected")
       exit(1)
    print(f"Gamepad detected: {devices.gamepads}")

# TODO: Threshold ABS buttons (sticks and trigers(LT, RT)) and Dpads
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
                cur_pressed.add(f"{btn_name}:{state}")
        
            print("Currently pressed:", cur_pressed)