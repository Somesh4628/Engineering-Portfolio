import time

import trimesh

from gaitform.__main__ import run_pipeline


def main():
    video_path = "sample_data/demo.mp4"
    scan_left = "data/orthotic.stl"
    scan_right = "data/orthotic.stl"
    pressure_csv = "data/demo_pressure.csv"

    print("--- STARTING DYNAMIC HEIGHT TEST ---")

    # Test 1: Short Patient (1.50m)
    print("\n[TEST 1] Patient Height: 1.50m")
    run_pipeline(
        video_path=video_path,
        height_m=1.50,
        scan_left=scan_left,
        scan_right=scan_right,
        shoe_size_mm=273.0,
        pressure_csv=pressure_csv,
    )
    # Wait a tiny bit for file system
    time.sleep(0.5)
    mesh_short = trimesh.load("orthotic_left.stl")
    height_short = mesh_short.bounds[1][2]
    print(f"Max Z-Height (Arch peak) for 1.50m patient: {height_short:.2f} mm")

    # Test 2: Tall Patient (2.00m)
    print("\n[TEST 2] Patient Height: 2.00m")
    run_pipeline(
        video_path=video_path,
        height_m=2.00,
        scan_left=scan_left,
        scan_right=scan_right,
        shoe_size_mm=273.0,
        pressure_csv=pressure_csv,
    )
    time.sleep(0.5)
    mesh_tall = trimesh.load("orthotic_left.stl")
    height_tall = mesh_tall.bounds[1][2]
    print(f"Max Z-Height (Arch peak) for 2.00m patient: {height_tall:.2f} mm")

    diff = height_tall - height_short
    print(
        f"\nTest complete! A taller patient gained {diff:.2f} mm of arch height automatically."
    )


if __name__ == "__main__":
    main()
