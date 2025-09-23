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
    single = [[b] for b in all_buttons]
    multi = generate_combinations()
    samples = (single + [idle]) * MIN_SAMPLES_PER_BUTTON + (multi + [idle]) * MIN_SAMPLES_PER_COMBO
    return samples
