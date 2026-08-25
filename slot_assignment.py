def assign_slots(prev_centers, hand_crops):
    """Returns (assigned_hand_crops_per_slot, updated_centers) -- assigned[i]
    is a HandCrop or None if slot i has nothing this frame.
 
    Matches globally by smallest distance first (not slot-by-slot in a fixed
    order) -- a naive "loop over slots, grab each one's nearest remaining
    crop" is wrong: slot 0 can steal a crop that's actually much closer to
    slot 1, if slot 0 happens to be considered first.
    """
    n_slots = len(prev_centers)
    assigned = [None] * n_slots
 
    def center_of(hc):
        x1, y1, x2, y2 = hc.crop_bounds
        return (x1 + x2) / 2, (y1 + y2) / 2
 
    crop_centers = [center_of(hc) for hc in hand_crops]
 
    candidates = []  # (distance, slot, crop_index) for every known-slot/crop pair
    for slot in range(n_slots):
        if prev_centers[slot] is None:
            continue
        px, py = prev_centers[slot]
        for ci, (cx, cy) in enumerate(crop_centers):
            candidates.append(((cx - px) ** 2 + (cy - py) ** 2, slot, ci))
    candidates.sort(key=lambda t: t[0])
 
    used_slots, used_crops = set(), set()
    for _, slot, ci in candidates:
        if slot in used_slots or ci in used_crops:
            continue
        assigned[slot] = hand_crops[ci]
        used_slots.add(slot)
        used_crops.add(ci)
 
    # Fill any still-empty slots with leftover crops (new hands, or slots with no prior center).
    leftover = [i for i in range(len(hand_crops)) if i not in used_crops]
    for slot in range(n_slots):
        if assigned[slot] is None and leftover:
            assigned[slot] = hand_crops[leftover.pop(0)]
 
    new_centers = list(prev_centers)
    for slot, hc in enumerate(assigned):
        if hc is not None:
            new_centers[slot] = center_of(hc)
    return assigned, new_centers
