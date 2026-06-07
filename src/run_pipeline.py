from pathlib import Path
import runpy
import sys
import traceback


REQUIRED_INPUT = Path("data/input.tif")


def run_step(name, func):
    print(f"\n=== {name} ===")
    try:
        func()
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"\nFailed: {name} (exit code {e.code})")
            sys.exit(e.code)
    except Exception:
        print(f"\nFailed: {name}")
        traceback.print_exc()
        sys.exit(1)
    print(f"Done: {name}")


def main():
    print("Starting satellite vegetation pipeline...")

    if not REQUIRED_INPUT.exists():
        print(
            f"ERROR: input file '{REQUIRED_INPUT}' not found.\n"
            f"Please run satveg from the project root, where data/input.tif exists."
        )
        sys.exit(2)

    from calculate_ndvi import main as calc_main
    from visualize_ndvi import main as vis_main

    run_step("Calculate NDVI and vegetation mask", calc_main)
    run_step("Generate NDVI preview image", vis_main)

    check_path = Path("checks/check_outputs.py")
    if not check_path.exists():
        print(f"ERROR: {check_path} not found.")
        sys.exit(2)
    run_step(
        "Check output files",
        lambda: runpy.run_path(str(check_path), run_name="__main__"),
    )

    print("\nPipeline completed successfully.")
    print("Outputs are saved in the outputs/ directory.")


if __name__ == "__main__":
    main()
