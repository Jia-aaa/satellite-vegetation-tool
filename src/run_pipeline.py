from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_step(name, command):
    print(f"\n=== {name} ===")
    result = subprocess.run(command, cwd=ROOT)

    if result.returncode != 0:
        print(f"\nFailed: {name}")
        sys.exit(result.returncode)

    print(f"Done: {name}")


def main():
    print("Starting satellite vegetation pipeline...")

    run_step(
        "Calculate NDVI and vegetation mask",
        [sys.executable, "src/calculate_ndvi.py"]
    )

    run_step(
        "Generate NDVI preview image",
        [sys.executable, "src/visualize_ndvi.py"]
    )

    run_step(
        "Check output files",
        [sys.executable, "src/check_outputs.py"]
    )

    print("\nPipeline completed successfully.")
    print("Outputs are saved in the outputs/ directory.")


if __name__ == "__main__":
    main()
