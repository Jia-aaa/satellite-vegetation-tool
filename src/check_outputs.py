from pathlib import Path

import numpy as np
import rasterio


NDVI_PATH = Path("outputs/ndvi.tif")
MASK_PATH = Path("outputs/vegetation_mask.tif")


def check_raster(path):
    path = Path(path)

    print(f"\n==============================")
    print(f"Checking: {path}")
    print(f"==============================")

    if not path.exists():
        print("ERROR: File does not exist.")
        return

    with rasterio.open(path) as src:
        print("=== Basic Info ===")
        print(f"Driver: {src.driver}")
        print(f"Width: {src.width}")
        print(f"Height: {src.height}")
        print(f"Band count: {src.count}")
        print(f"CRS: {src.crs}")
        print(f"Transform: {src.transform}")
        print(f"Bounds: {src.bounds}")
        print(f"Data types: {src.dtypes}")
        print(f"NoData values: {src.nodatavals}")
        print(f"Descriptions: {src.descriptions}")

        data = src.read(1)
        nodata = src.nodatavals[0]

        if nodata is not None:
            valid_mask = data != nodata
        else:
            valid_mask = np.ones(data.shape, dtype=bool)

        valid_data = data[valid_mask]

        print("\n=== Pixel Statistics ===")
        print(f"Total pixels: {data.size}")
        print(f"Valid pixels: {valid_data.size}")
        print(f"NoData pixels: {data.size - valid_data.size}")

        if valid_data.size > 0:
            print(f"Min: {float(np.min(valid_data))}")
            print(f"Max: {float(np.max(valid_data))}")
            print(f"Mean: {float(np.mean(valid_data))}")
            print(f"Std: {float(np.std(valid_data))}")

        unique_values = np.unique(data)

        print("\n=== Unique Values ===")
        if unique_values.size <= 30:
            print(f"All unique values: {unique_values}")
        else:
            print(f"Unique value count: {unique_values.size}")
            print(f"First 30 unique values: {unique_values[:30]}")

        print("\n=== Checks ===")

        if src.driver == "GTiff":
            print("OK: Driver is GTiff")
        else:
            print("WARNING: Driver is not GTiff")

        if src.width == 100 and src.height == 100:
            print("OK: Size is 100 x 100")
        else:
            print("WARNING: Size is not 100 x 100")

        if src.count == 1:
            print("OK: Band count is 1")
        else:
            print("WARNING: Band count is not 1")

        if str(src.crs) == "EPSG:32650":
            print("OK: CRS is EPSG:32650")
        else:
            print(f"WARNING: CRS is {src.crs}")


def check_ndvi():
    print("\n\n################################")
    print("NDVI FILE CHECK")
    print("################################")

    check_raster(NDVI_PATH)

    with rasterio.open(NDVI_PATH) as src:
        data = src.read(1)
        nodata = src.nodatavals[0]
        valid_data = data[data != nodata]

        print("\n=== NDVI Specific Checks ===")

        if src.dtypes[0] == "float32":
            print("OK: NDVI dtype is float32")
        else:
            print(f"WARNING: NDVI dtype is {src.dtypes[0]}")

        if nodata == -9999.0:
            print("OK: NDVI nodata is -9999")
        else:
            print(f"WARNING: NDVI nodata is {nodata}")

        if valid_data.size > 0:
            ndvi_min = float(np.min(valid_data))
            ndvi_max = float(np.max(valid_data))

            if ndvi_min >= -1.0 and ndvi_max <= 1.0:
                print("OK: NDVI values are within [-1, 1]")
            else:
                print(f"WARNING: NDVI out of range. min={ndvi_min}, max={ndvi_max}")


def check_mask():
    print("\n\n################################")
    print("VEGETATION MASK FILE CHECK")
    print("################################")

    check_raster(MASK_PATH)

    with rasterio.open(MASK_PATH) as src:
        data = src.read(1)
        nodata = src.nodatavals[0]
        unique_values = set(np.unique(data).tolist())

        print("\n=== Mask Specific Checks ===")

        if src.dtypes[0] == "uint8":
            print("OK: Mask dtype is uint8")
        else:
            print(f"WARNING: Mask dtype is {src.dtypes[0]}")

        if nodata == 255:
            print("OK: Mask nodata is 255")
        else:
            print(f"WARNING: Mask nodata is {nodata}")

        allowed_values = {0, 1, 255}
        if unique_values.issubset(allowed_values):
            print("OK: Mask only contains 0, 1, and 255")
        else:
            print(f"WARNING: Mask has unexpected values: {unique_values}")

        vegetation_count = int(np.sum(data == 1))
        non_vegetation_count = int(np.sum(data == 0))
        nodata_count = int(np.sum(data == 255))

        print("\n=== Mask Counts ===")
        print(f"Vegetation pixels, value 1: {vegetation_count}")
        print(f"Non-vegetation pixels, value 0: {non_vegetation_count}")
        print(f"NoData pixels, value 255: {nodata_count}")


def main():
    check_ndvi()
    check_mask()


if __name__ == "__main__":
    main()