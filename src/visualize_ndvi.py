from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio


def main():
    input_path = Path("outputs/ndvi.tif")
    output_dir = Path("outputs")
    output_path = output_dir / "ndvi_preview.png"

    if not input_path.exists():
        raise FileNotFoundError(
            f"找不到 NDVI 文件: {input_path}，请先运行 python src/calculate_ndvi.py"
        )

    output_dir.mkdir(exist_ok=True)

    with rasterio.open(input_path) as src:
        ndvi = src.read(1)
        nodata = src.nodata

    if nodata is not None:
        ndvi = np.where(ndvi == nodata, np.nan, ndvi)

    plt.figure(figsize=(8, 6))

    image = plt.imshow(
        ndvi,
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
    )

    plt.colorbar(image, label="NDVI")
    plt.title("NDVI Preview")
    plt.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    valid_ndvi = ndvi[~np.isnan(ndvi)]

    print("=== NDVI Preview Generated ===")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Valid pixels: {valid_ndvi.size}")
    print(f"NDVI min: {valid_ndvi.min()}")
    print(f"NDVI max: {valid_ndvi.max()}")
    print(f"NDVI mean: {valid_ndvi.mean()}")


if __name__ == "__main__":
    main()