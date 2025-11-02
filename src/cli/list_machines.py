# python -m src.cli.list_machines --file data/node_disk_io_time_seconds_total/1754002800.0.json.gz
# python -m src.cli.list_machines --file1 data/node_disk_io_time_seconds_total/1754002800.0.json.gz --file2 data/rPDULoadStatusLoad/1754002800.0.json.gz

import argparse
from src.load_prometheus import list_machines

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", help="Single file to list machines from")
    p.add_argument("--file1", help="First file for comparison")
    p.add_argument("--file2", help="Second file for comparison")
    args = p.parse_args()

    if args.file1 and args.file2:
        machines1 = dict(list_machines(args.file1))
        machines2 = dict(list_machines(args.file2))
        
        all_machines = set(machines1.keys()) | set(machines2.keys())
        common = set(machines1.keys()) & set(machines2.keys())
        
        print(f"File 1: {args.file1}")
        print(f"  {len(machines1)} machines, {sum(machines1.values())} total data points")
        print(f"\nFile 2: {args.file2}")
        print(f"  {len(machines2)} machines, {sum(machines2.values())} total data points")
        print(f"\nCommon machines (have data in both files): {len(common)}")
        
        if common:
            print("\nMachines with data in both files (recommended for analysis):")
            for m in sorted(common):
                count1 = machines1.get(m, 0)
                count2 = machines2.get(m, 0)
                print(f"  {m}")
                print(f"    File 1: {count1} points, File 2: {count2} points")
        
        only_file1 = set(machines1.keys()) - set(machines2.keys())
        only_file2 = set(machines2.keys()) - set(machines1.keys())
        
        if only_file1:
            print(f"\nMachines only in file 1 ({len(only_file1)}):")
            for m in sorted(only_file1):
                print(f"  {m} ({machines1[m]} points)")
        
        if only_file2:
            print(f"\nMachines only in file 2 ({len(only_file2)}):")
            for m in sorted(only_file2):
                print(f"  {m} ({machines2[m]} points)")
    elif args.file:
        machines = list_machines(args.file)
        
        print(f"Found {len(machines)} unique machines in {args.file}:")
        print(f"Total data points: {sum(count for _, count in machines)}")
        print()
        for m, count in machines:
            print(f"  {m}: {count} points")
    else:
        p.print_help()

if __name__ == "__main__":
    main()