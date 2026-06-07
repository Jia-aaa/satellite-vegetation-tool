"""
手算对拍：从 input.tif 直接读 3 个有效像素的 DN，
按公式手算 NDVI，再和 outputs/ndvi.tif 里同位置的值比较。

reflectance = DN * scale + offset
NDVI = (NIR_ref - Red_ref) / (NIR_ref + Red_ref)
"""
from pathlib import Path

import numpy as np
import rasterio


INPUT_PATH = Path("data/input.tif")
NDVI_PATH = Path("outputs/ndvi.tif")

RED_BAND = 1
NIR_BAND = 2


def main():
    with rasterio.open(INPUT_PATH) as src:
        tags = src.tags()
        scale = float(tags.get("SCALE", 1.0))
        offset = float(tags.get("OFFSET", 0.0))

        red_dn = src.read(RED_BAND)
        nir_dn = src.read(NIR_BAND)
        red_nodata = src.nodatavals[RED_BAND - 1]
        nir_nodata = src.nodatavals[NIR_BAND - 1]

    with rasterio.open(NDVI_PATH) as dst:
        ndvi_arr = dst.read(1)
        ndvi_nodata = dst.nodata

    valid = (red_dn != red_nodata) & (nir_dn != nir_nodata)
    ys, xs = np.where(valid)

    # 选 3 个分散的有效像素：第一个、中间一个、最后一个
    n = len(ys)
    picks = [0, n // 2, n - 1]

    print("=== Manual pixel check ===")
    print(f"scale = {scale}")
    print(f"offset = {offset}")
    print(f"red_nodata = {red_nodata}, nir_nodata = {nir_nodata}")
    print(f"ndvi_nodata = {ndvi_nodata}")
    print(f"total valid pixels = {n}")
    print()

    max_diff = 0.0
    for i, p in enumerate(picks, 1):
        y, x = int(ys[p]), int(xs[p])
        rd = float(red_dn[y, x])
        nd = float(nir_dn[y, x])
        red_ref = rd * scale + offset
        nir_ref = nd * scale + offset
        manual = (nir_ref - red_ref) / (nir_ref + red_ref)
        manual_clipped = float(np.clip(manual, -1.0, 1.0))
        code = float(ndvi_arr[y, x])
        diff = abs(manual_clipped - code)
        max_diff = max(max_diff, diff)
        print(f"Pixel {i}: row={y}, col={x}")
        print(f"  Red DN  = {rd}")
        print(f"  NIR DN  = {nd}")
        print(f"  Red ref = {red_ref:.8f}")
        print(f"  NIR ref = {nir_ref:.8f}")
        print(f"  manual NDVI = {manual_clipped:.8f}")
        print(f"  code   NDVI = {code:.8f}")
        print(f"  abs diff    = {diff:.2e}")
        print()

    print(f"Max abs diff over 3 pixels: {max_diff:.2e}")
    if max_diff < 1e-5:
        print("RESULT: OK (within float tolerance)")
    else:
        print("RESULT: MISMATCH - check formula or band order")


if __name__ == "__main__":
    main()
