"""
独立对拍：用 rasterio 重新读 input.tif 和 outputs/ndvi.tif，
独立检查范围、地理参考、形状是否一致。
"""
from pathlib import Path

import numpy as np
import rasterio


INPUT_PATH = Path("data/input.tif")
NDVI_PATH = Path("outputs/ndvi.tif")


def main():
    print("=== Validation report ===\n")

    with rasterio.open(INPUT_PATH) as src:
        in_crs = src.crs
        in_transform = src.transform
        in_shape = (src.height, src.width)
        print(f"input file      : {INPUT_PATH}")
        print(f"input shape     : {in_shape}")
        print(f"input crs       : {in_crs}")
        print(f"input transform : {in_transform}")
        print()

    with rasterio.open(NDVI_PATH) as dst:
        ndvi = dst.read(1)
        ndvi_nodata = dst.nodata
        nd_crs = dst.crs
        nd_transform = dst.transform
        nd_shape = (dst.height, dst.width)
        print(f"ndvi file       : {NDVI_PATH}")
        print(f"ndvi shape      : {nd_shape}")
        print(f"ndvi crs        : {nd_crs}")
        print(f"ndvi transform  : {nd_transform}")
        print(f"ndvi nodata     : {ndvi_nodata}")
        print()

    valid = ndvi != ndvi_nodata
    valid_vals = ndvi[valid]

    ndvi_min = float(np.min(valid_vals))
    ndvi_max = float(np.max(valid_vals))

    print("=== Range check ===")
    print(f"valid pixels : {int(valid.sum())}")
    print(f"ndvi min     : {ndvi_min}")
    print(f"ndvi max     : {ndvi_max}")
    if -1.0 <= ndvi_min and ndvi_max <= 1.0:
        print("range ok: NDVI in [-1, 1]")
    else:
        print("range FAIL: NDVI out of [-1, 1]")
    print()

    print("=== Geo reference check ===")
    crs_ok = in_crs == nd_crs
    tr_ok = in_transform == nd_transform
    shape_ok = in_shape == nd_shape
    print(f"crs match       : {crs_ok}")
    print(f"transform match : {tr_ok}")
    print(f"shape match     : {shape_ok}")
    if crs_ok and tr_ok and shape_ok:
        print("geo ref ok")
    else:
        print("geo ref FAIL")


if __name__ == "__main__":
    main()
