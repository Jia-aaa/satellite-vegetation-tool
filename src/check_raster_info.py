from pathlib import Path

import numpy as np
import rasterio


def print_dict(title, data):
    """
    打印字典类型的元数据。
    如果字典为空，也明确告诉用户没有元数据。
    """
    print(f"\n=== {title} ===")

    if not data:
        print("No tags found.")
        return

    for key, value in data.items():
        print(f"{key}: {value}")


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

        print("\n=== Raster Spatial Info ===")
        print(f"Resolution: {src.res}")
        print(f"Coordinate reference system: {src.crs}")
        print(f"Is georeferenced: {src.transform is not None}")

        print("\n=== Dataset Metadata ===")
        print(f"Descriptions: {src.descriptions}")
        print(f"Scales: {src.scales}")
        print(f"Offsets: {src.offsets}")
        print(f"Units: {src.units}")
        print(f"Color interpretations: {src.colorinterp}")

        print_dict("Dataset Tags", src.tags())

        print("\n=== Band Details ===")

        for band_index in range(1, src.count + 1):
            print(f"\n--- Band {band_index} Metadata ---")
            print(f"Description: {src.descriptions[band_index - 1]}")
            print(f"Data type: {src.dtypes[band_index - 1]}")
            print(f"NoData: {src.nodatavals[band_index - 1]}")
            print(f"Scale: {src.scales[band_index - 1]}")
            print(f"Offset: {src.offsets[band_index - 1]}")
            print(f"Unit: {src.units[band_index - 1]}")
            print(f"Color interpretation: {src.colorinterp[band_index - 1]}")

            band_tags = src.tags(band_index)
            if band_tags:
                print("Band tags:")
                for key, value in band_tags.items():
                    print(f"  {key}: {value}")
            else:
                print("Band tags: No tags found.")

            print(f"\n--- Band {band_index} Statistics ---")

            band = src.read(band_index).astype("float32")
            nodata = src.nodatavals[band_index - 1]
            scale = src.scales[band_index - 1]
            offset = src.offsets[band_index - 1]

            if nodata is not None:
                valid_mask = band != nodata
            else:
                valid_mask = np.ones(band.shape, dtype=bool)

            valid_values = band[valid_mask]

            if valid_values.size == 0:
                print("  No valid pixels found.")
                continue

            print("Raw values:")
            print(f"  min: {np.min(valid_values)}")
            print(f"  max: {np.max(valid_values)}")
            print(f"  mean: {np.mean(valid_values)}")
            print(f"  std: {np.std(valid_values)}")

            # 如果 scale / offset 不为空，则计算转换后的值
            # rasterio 默认 scale 通常是 1.0，offset 通常是 0.0
            actual_values = valid_values * scale + offset

            print("Scaled values:")
            print(f"  min: {np.min(actual_values)}")
            print(f"  max: {np.max(actual_values)}")
            print(f"  mean: {np.mean(actual_values)}")
            print(f"  std: {np.std(actual_values)}")

        print("\n=== Preliminary NDVI Band Assumption ===")

        if src.count >= 2:
            print("This raster has at least 2 bands.")
            print("For the first version of the NDVI tool, we can assume:")
            print("  Band 1 = Red")
            print("  Band 2 = NIR")
            print("")
            print("But this assumption should be confirmed using:")
            print("  1. Band descriptions")
            print("  2. Band tags")
            print("  3. Dataset metadata")
            print("  4. Data provider / advisor documentation")
        else:
            print("This raster has fewer than 2 bands, so NDVI cannot be calculated directly.")


if __name__ == "__main__":
    main()