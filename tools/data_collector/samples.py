from .config import *

def generate_combinations():
    multi = []
    for face in face_buttons:
        for movement in dpad + ls + rs:
            multi.append([face, movement])
            for trig in triggers + bumpers:
                multi.append([movement, trig])
                multi.append([face, movement, trig])
    # Stick diagonals
    direction = [["Up", "Left"], ["Up", "Right"], ["Down", "Left"], ["Down", "Right"]]
    for move in ["LS", "RS"]:
        for d in direction:
            multi.append([f"{move}_{d[0]}+{move}_{d[1]}"])
    for b in bumpers:
        for t in triggers:
            multi.append([b, t])
    return multi

def generate_samples():
    single = [[b] for b in ALL_BUTTONS]
    multi = generate_combinations()
    return single+multi

def update_remaining(remaining, counters):
    for b, count in counters.items():
        if b in remaining:
            if (len(b) == 1 and count >= MIN_SAMPLES_PER_BUTTON) or (len(b) > 1 and count >= MIN_SAMPLES_PER_COMBO):
                remaining.remove(b)
    return remaining