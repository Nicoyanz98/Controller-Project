def _center_of(hand_crop):
    x1, y1, x2, y2 = hand_crop.crop_bounds
    return (x1 + x2) / 2, (y1 + y2) / 2


def assign_slots(slot_state, hand_crops):
    """
    `slot_state`: n slots list where each entry is either None or a dict {'track_id': int or None, 'center': (x, y)}

    Returns (assigned, new_slot_state)
      assigned[i]: the HandCrop now in slot i
      new_slot_state: slot_state updated with whatever ended up in each slot
    """
    n_slots = len(slot_state)
    assigned = [None] * n_slots
    remaining = list(hand_crops)

    # Keeps crops in the last-known slot with the same track_id
    _match_by_track_id(slot_state, remaining, assigned)
    # If no track_id is available, fall back to nearest-previous-center slot matching
    _match_by_position(slot_state, remaining, assigned)
    # Left over hand crops are assigned in empty slots.
    _fill_empty_slots(remaining, assigned)
 
    new_state = list(slot_state)
    for slot, hc in enumerate(assigned):
        if hc is not None:
            new_state[slot] = {"track_id": hc.track_id, "center": _center_of(hc)}
    return assigned, new_state

def _match_by_track_id(slot_state, remaining, assigned):
    for slot, st in enumerate(slot_state):
        if st is None or st.get("track_id") is None:
            continue
        match = next((hc for hc in remaining if hc.track_id == st["track_id"]), None)
        if match is not None:
            assigned[slot] = match
            remaining.remove(match)

def _match_by_position(slot_state, remaining, assigned):
    candidates = []  # (distance, slot, crop_index)
    for slot, st in enumerate(slot_state):
        if assigned[slot] is not None or st is None or st.get("center") is None:
            continue
        px, py = st["center"]
        for i, hc in enumerate(remaining):
            cx, cy = _center_of(hc)
            candidates.append(((cx - px) ** 2 + (cy - py) ** 2, slot, i))
    candidates.sort(key=lambda t: t[0])
 
    used_slots, used_idx = set(), set()
    for _, slot, i in candidates:
        if slot in used_slots or i in used_idx:
            continue
        assigned[slot] = remaining[i]
        used_slots.add(slot)
        used_idx.add(i)
 
    for i in sorted(used_idx, reverse=True):
        del remaining[i]

def _fill_empty_slots(remaining, assigned):
    for slot in range(len(assigned)):
        if assigned[slot] is None and remaining:
            assigned[slot] = remaining.pop(0)
