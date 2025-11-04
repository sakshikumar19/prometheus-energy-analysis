import argparse
from src.analyze_pair import analyze_pair
import sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file1", required=True)
    p.add_argument("--file2", required=True)
    p.add_argument("--outdir", default="results")
    p.add_argument("--machine", required=True, help="Machine filter (substring OK)")
    p.add_argument("--metric1", default="Disk IO", help="Label for metric 1")
    p.add_argument("--metric2", default="Power", help="Label for metric 2")
    p.add_argument("--hours", type=int, default=12, help="Hours in window")
    p.add_argument("--start", help="ISO start time (UTC)")
    p.add_argument("--end", help="ISO end time (UTC)")
    args = p.parse_args()

    # Run the simple pair analysis
    res = analyze_pair(
        args.machine,
        args.file1,
        args.file2,
        args.metric1,
        args.metric2,
        args.outdir,
        args.hours,
        window_start=args.start,
        window_end=args.end,
    )
    if res is None:
        print("No results (empty or unaligned data)")
        sys.exit(1)
    print(f"Saved to {res['dir']}")

if __name__ == "__main__":
    main()