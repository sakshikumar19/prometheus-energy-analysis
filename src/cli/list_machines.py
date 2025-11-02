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

