from pathlib import Path

import numpy as np
import rasterio


def main():
    input_path = Path("data/input.tif")
    output_dir = Path("output")
    output_path = output_dir / "ndvi.tif"

    output_dir.mkdir(exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"找不到文件: {input_path}")

    with rasterio.open(input_path) as src:
        if src.count < 2:
            raise ValueError("输入影像至少需要 2 个波段：Red 和 NIR")

        # 根据前一步检查结果，暂定：
        # Band 1 = Red
        # Band 2 = NIR
        red = src.read(1).astype("float32")
        nir = src.read(2).astype("float32")

        nodata_red = src.nodatavals[0]
        nodata_nir = src.nodatavals[1]

        valid_mask = np.ones(red.shape, dtype=bool)

        if nodata_red is not None:
            valid_mask &= red != nodata_red

        if nodata_nir is not None:
            valid_mask &= nir != nodata_nir

        denominator = nir + red
        valid_mask &= denominator != 0

        ndvi = np.full(red.shape, -9999.0, dtype="float32")
        ndvi[valid_mask] = (nir[valid_mask] - red[valid_mask]) / denominator[valid_mask]

        profile = src.profile.copy()
        profile.update(
            dtype="float32",
            count=1,
            nodata=-9999.0,
            compress="lzw"
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(ndvi, 1)

    valid_ndvi = ndvi[ndvi != -9999.0]

    print("=== NDVI Calculation Finished ===")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"NDVI min: {valid_ndvi.min()}")
    print(f"NDVI max: {valid_ndvi.max()}")
    print(f"NDVI mean: {valid_ndvi.mean()}")


if __name__ == "__main__":
    main()