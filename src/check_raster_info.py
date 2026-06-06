from pathlib import Path

import numpy as np
import rasterio


def main():
    input_path = Path("data/input.tif")

    if not input_path.exists():
        raise FileNotFoundError(f"找不到文件: {input_path}")

    with rasterio.open(input_path) as src:
        print("=== Raster Basic Info ===")
        print(f"File: {input_path}")
        print(f"Driver: {src.driver}")
        print(f"Width: {src.width}")
        print(f"Height: {src.height}")
        print(f"Band count: {src.count}")
        print(f"CRS: {src.crs}")
        print(f"Transform: {src.transform}")
        print(f"Bounds: {src.bounds}")
        print(f"Data types: {src.dtypes}")
        print(f"NoData values: {src.nodatavals}")

        print("\n=== Band Statistics ===")

        for band_index in range(1, src.count + 1):
            band = src.read(band_index).astype("float32")
            nodata = src.nodatavals[band_index - 1]

            if nodata is not None:
                band = np.where(band == nodata, np.nan, band)

            print(f"\nBand {band_index}:")
            print(f"  min: {np.nanmin(band)}")
            print(f"  max: {np.nanmax(band)}")
            print(f"  mean: {np.nanmean(band)}")
            print(f"  std: {np.nanstd(band)}")


if __name__ == "__main__":
    main()