import subprocess
import sys

def main():
    print("Delegating to backend/run_extraction.py ...\n")
    subprocess.run([sys.executable, "backend/run_extraction.py", "--input", "data/raw", "--output", "data/exports"])

if __name__ == "__main__":
    main()
