import numpy as np

WRIST = 0
N_SLOTS = 2


class SlotAssigner:
    """Gives each detected hand a fixed slot (0 or 1) across the frames of a clip.

    MediaPipe returns hands in any order and its Left/Right label assumes a mirrored
    image, so the slot is chosen by mode:
        image_x            two hands: slot 0 = smaller wrist x. One hand: the slot whose
                           last position is closest, or by image half if none is known
        mediapipe          slot 0 = MediaPipe "Left", slot 1 = "Right"
        mediapipe_swapped  the reverse
    """

    def __init__(self, mode, max_age=15):
        self.mode = mode
        self.max_age = max_age

        # Last wrist position per slot, forgotten after max_age frames without the hand
        self.last = [None, None]
        self.age = [0, 0]

    def assign(self, hands):
        """Returns a list of (slot, hand) with at most one hand per slot."""
        hands = sorted(hands, key=lambda hand: -hand["score"])[:N_SLOTS]
        if self.mode in ("mediapipe", "mediapipe_swapped"):
            pairs = self._by_label(hands)
        else:
            pairs = self._by_position(hands)

        for slot in range(N_SLOTS):
            self.age[slot] += 1
        for slot, hand in pairs:
            self.last[slot] = hand["img"][WRIST, :2].copy()
            self.age[slot] = 0
        for slot in range(N_SLOTS):
            if self.age[slot] > self.max_age:
                self.last[slot] = None
        return pairs

    def _by_label(self, hands):
        swapped = self.mode == "mediapipe_swapped"
        slots = []
        for hand in hands:
            if swapped and hand["label"] != -1:
                slots.append(1 - hand["label"])
            else:
                slots.append(hand["label"])

        # Missing or conflicting labels fall back to the position
        if -1 in slots:
            return self._by_position(hands)
        if len(slots) == 2 and slots[0] == slots[1]:
            return self._by_position(hands)
        return list(zip(slots, hands))

    def _by_position(self, hands):
        if len(hands) == 2:
            left_hand, right_hand = sorted(hands, key=lambda hand: hand["img"][WRIST, 0])
            return [(0, left_hand), (1, right_hand)]

        if len(hands) == 1:
            wrist = hands[0]["img"][WRIST, :2]
            known = []
            for slot in range(N_SLOTS):
                if self.last[slot] is not None:
                    known.append((np.linalg.norm(wrist - self.last[slot]), slot))

            if not known:
                slot = 0 if wrist[0] < 0.5 else 1
                return [(slot, hands[0])]

            distance, slot = min(known)
            other = 1 - slot
            # Far from slot and the other slot is free: probably the other hand
            if self.last[other] is None and distance > 0.25:
                slot = other
            return [(slot, hands[0])]
        return []
