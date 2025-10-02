import sys
from data_collector.collector import run_collector

if __name__ == "__main__":
    run_collector(connected=("-C" in sys.argv[1:]))
