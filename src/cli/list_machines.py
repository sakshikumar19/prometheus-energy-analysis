# python -m src.cli.list_machines --file data/node_disk_io_time_seconds_total/1754002800.0.json.gz

import argparse
from src.load_prometheus import list_machines

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    args = p.parse_args()

    machines = list_machines(args.file)
    
    print(f"Found {len(machines)} unique machines:")
    for m in machines:
        print(f"  {m}")

if __name__ == "__main__":
    main()