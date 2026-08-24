import argparse

from results_store import load_results
from visualizer import HandVisualizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, help="results store .pkl file")
    parser.add_argument("--out_html", default="hand_visualization.html")
    parser.add_argument("--mano_pkl", default=None)
    parser.add_argument("--only", nargs="*", default=None, help="optional list of hand_ids to include (default: all in the store)")
    args = parser.parse_args()

    results = load_results(args.results)
    if not results:
        print(f"'{args.results}' has no results yet -- run run_pipeline.py first.")
        return

    if args.only:
        missing = set(args.only) - set(results)
        if missing:
            print(f"Warning: hand_id(s) not found in store, skipping: {sorted(missing)}")
        results = {k: v for k, v in results.items() if k in args.only}

    mano_faces = HandVisualizer.load_mano_faces(args.mano_pkl) if args.mano_pkl else None
    HandVisualizer(mano_faces=mano_faces).add_results(list(results.values())).save_html(args.out_html)


if __name__ == "__main__":
    main()
