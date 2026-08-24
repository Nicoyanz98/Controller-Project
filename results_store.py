import pickle
from pathlib import Path
from typing import Dict, List, Union

from inference_result import InferenceResult


def load_results(path: Union[str, Path]) -> Dict[str, InferenceResult]:
    """Load the results store. Returns {} if the file doesn't exist yet (first run)."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        raw = pickle.load(f)
    return {hand_id: InferenceResult.from_dict(d) for hand_id, d in raw.items()}


def save_results(results: Union[List[InferenceResult], Dict[str, InferenceResult]], path: Union[str, Path], merge: bool = True) -> Dict[str, InferenceResult]:
    """
    Write results to `path`. Returns the full merged dict of results.

    `merge=True` (default): load whatever is already at `path` first and update it with the new results, so results accumulate
    across multiple images/runs into one store instead of each run overwriting the last.
    
    Re-saving a hand_id that already exists replaces that hand's entry.
    """
    if isinstance(results, list):
        results = {r.hand_id: r for r in results}

    existing = load_results(path) if merge else {}
    existing.update(results)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({hand_id: r.to_dict() for hand_id, r in existing.items()}, f)

    return existing
