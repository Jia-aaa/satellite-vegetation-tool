"""
输出验收：对比 outputs/ 下的成果与 data/input.tif 的元数据，
做硬断言检查。任一项失败则非零退出。

覆盖 SPEC.md 的验收标准 1, 2, 3, 5, 6（第 4 条手算由 manual_pixel_check.py 覆盖）。
"""
from pathlib import Path
import json
import sys

import numpy as np
import rasterio


INPUT_PATH = Path("data/input.tif")
NDVI_PATH = Path("outputs/ndvi.tif")
MASK_PATH = Path("outputs/vegetation_mask.tif")
STATS_PATH = Path("outputs/stats.json")
PREVIEW_PATH = Path("outputs/ndvi_preview.png")


def fail(msg, errors):
    print(f"FAIL: {msg}")
    errors.append(msg)


def ok(msg):
    print(f"OK: {msg}")


def check_files_exist(errors):
    print("\n=== File existence ===")
    for p in (NDVI_PATH, MASK_PATH, STATS_PATH, PREVIEW_PATH):
        if p.exists():
            ok(f"{p} exists")
        else:
            fail(f"{p} missing", errors)


def check_ndvi(input_meta, errors):
    print("\n=== NDVI raster ===")
    if not NDVI_PATH.exists():
        return
    with rasterio.open(NDVI_PATH) as src:
        if src.driver == "GTiff":
            ok("driver is GTiff")
        else:
            fail(f"driver is {src.driver}, not GTiff", errors)

        if src.count == 1:
            ok("band count is 1")
        else:
            fail(f"band count is {src.count}, expected 1", errors)

        if src.dtypes[0] == "float32":
            ok("dtype is float32")
        else:
            fail(f"dtype is {src.dtypes[0]}, expected float32", errors)

        if src.nodata == -9999.0:
            ok("nodata is -9999.0")
        else:
            fail(f"nodata is {src.nodata}, expected -9999.0", errors)

        if src.crs == input_meta["crs"]:
            ok(f"CRS matches input ({src.crs})")
        else:
            fail(f"CRS {src.crs} != input {input_meta['crs']}", errors)

        if src.transform == input_meta["transform"]:
            ok("transform matches input")
        else:
            fail("transform does not match input", errors)

        if (src.height, src.width) == input_meta["shape"]:
            ok(f"shape matches input {(src.height, src.width)}")
        else:
            fail(
                f"shape {(src.height, src.width)} != input {input_meta['shape']}",
                errors,
            )

        data = src.read(1)
        valid = data[data != src.nodata]
        if valid.size == 0:
            fail("no valid NDVI pixels", errors)
            return
        ndvi_min = float(np.min(valid))
        ndvi_max = float(np.max(valid))
        if -1.0 <= ndvi_min and ndvi_max <= 1.0:
            ok(f"valid NDVI in [-1, 1]  (min={ndvi_min:.6f}, max={ndvi_max:.6f})")
        else:
            fail(f"NDVI out of [-1, 1]: min={ndvi_min}, max={ndvi_max}", errors)


def check_mask(input_meta, errors):
    print("\n=== Vegetation mask ===")
    if not MASK_PATH.exists():
        return
    with rasterio.open(MASK_PATH) as src:
        if src.dtypes[0] == "uint8":
            ok("dtype is uint8")
        else:
            fail(f"dtype is {src.dtypes[0]}, expected uint8", errors)

        if src.nodata == 255:
            ok("nodata is 255")
        else:
            fail(f"nodata is {src.nodata}, expected 255", errors)

        if src.crs == input_meta["crs"]:
            ok(f"CRS matches input ({src.crs})")
        else:
            fail(f"CRS {src.crs} != input {input_meta['crs']}", errors)

        if src.transform == input_meta["transform"]:
            ok("transform matches input")
        else:
            fail("transform does not match input", errors)

        if (src.height, src.width) == input_meta["shape"]:
            ok(f"shape matches input {(src.height, src.width)}")
        else:
            fail(
                f"shape {(src.height, src.width)} != input {input_meta['shape']}",
                errors,
            )

        mask = src.read(1)
        unique = set(int(v) for v in np.unique(mask).tolist())
        if unique.issubset({0, 1, 255}):
            ok(f"mask values subset of {{0,1,255}}: {sorted(unique)}")
        else:
            fail(f"mask has unexpected values: {sorted(unique)}", errors)

        return mask


def check_stats(mask, input_meta, errors):
    print("\n=== Stats / mask consistency ===")
    if not STATS_PATH.exists() or mask is None:
        return
    with open(STATS_PATH, "r", encoding="utf-8") as f:
        stats = json.load(f)

    veg = int(np.sum(mask == 1))
    non = int(np.sum(mask == 0))
    nd = int(np.sum(mask == 255))

    valid_count = stats.get("valid_pixel_count")
    nodata_count = stats.get("nodata_pixel_count")
    h, w = input_meta["shape"]
    total_expected = h * w

    if veg + non == valid_count:
        ok(f"mask 0+1 ({veg + non}) == stats.valid_pixel_count ({valid_count})")
    else:
        fail(
            f"mask 0+1 ({veg + non}) != stats.valid_pixel_count ({valid_count})",
            errors,
        )

    if valid_count + nodata_count == total_expected:
        ok(
            f"valid+nodata ({valid_count + nodata_count}) == width*height ({total_expected})"
        )
    else:
        fail(
            f"valid+nodata ({valid_count + nodata_count}) != width*height ({total_expected})",
            errors,
        )

    if nd == nodata_count:
        ok(f"mask 255 count ({nd}) == stats.nodata_pixel_count ({nodata_count})")
    else:
        fail(
            f"mask 255 count ({nd}) != stats.nodata_pixel_count ({nodata_count})",
            errors,
        )


def main():
    print("################################")
    print("Output acceptance checks")
    print("################################")

    if not INPUT_PATH.exists():
        print(f"FAIL: input file {INPUT_PATH} not found, cannot validate.")
        sys.exit(2)

    with rasterio.open(INPUT_PATH) as src:
        input_meta = {
            "crs": src.crs,
            "transform": src.transform,
            "shape": (src.height, src.width),
        }
    print(f"input crs       : {input_meta['crs']}")
    print(f"input transform : {input_meta['transform']}")
    print(f"input shape     : {input_meta['shape']}")

    errors = []
    check_files_exist(errors)
    check_ndvi(input_meta, errors)
    mask = check_mask(input_meta, errors)
    check_stats(mask, input_meta, errors)

    print("\n=== Summary ===")
    if errors:
        print(f"FAILED: {len(errors)} check(s) did not pass:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("All output acceptance checks passed.")


if __name__ == "__main__":
    main()
