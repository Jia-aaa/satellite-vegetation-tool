from pathlib import Path
import json

import numpy as np
import rasterio


# 输入文件
INPUT_PATH = Path("data/input.tif")

# 输出文件夹
OUTPUT_DIR = Path("outputs")

# 输出文件
NDVI_PATH = OUTPUT_DIR / "ndvi.tif"
MASK_PATH = OUTPUT_DIR / "vegetation_mask.tif"
STATS_PATH = OUTPUT_DIR / "stats.json"


# 根据元数据确认：
# Band 1 = Red
# Band 2 = NIR
RED_BAND = 1
NIR_BAND = 2


# 输出 NDVI 的 nodata 值
# 因为 NDVI 正常范围是 -1 到 1，所以用 -9999 表示无效值
OUTPUT_NODATA = -9999.0


# 植被判断阈值
# NDVI >= 0.3 认为是植被
VEGETATION_THRESHOLD = 0.3


def get_scale_offset(src):
    """
    从 input.tif 的 metadata tags 中读取 SCALE 和 OFFSET。

    你的文件里有：
        SCALE = 2.75e-05
        OFFSET = -0.2

    注意：
    这两个值不是在 src.scales / src.offsets 里面，
    而是在 src.tags() 里面。
    """
    tags = src.tags()

    scale = float(tags.get("SCALE", 1.0))
    offset = float(tags.get("OFFSET", 0.0))

    return scale, offset


def main():
    """
    主流程：
    1. 检查输入文件是否存在
    2. 创建 outputs 文件夹
    3. 读取 Red 和 NIR
    4. 处理 nodata
    5. 处理 scale 和 offset
    6. 计算 NDVI
    7. 生成 vegetation_mask
    8. 写出 ndvi.tif
    9. 写出 vegetation_mask.tif
    10. 写出 stats.json
    """

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"找不到输入文件: {INPUT_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(INPUT_PATH) as src:
        print("=== NDVI Calculation Started ===")
        print(f"Input file: {INPUT_PATH}")

        # 检查波段数量
        if src.count < 2:
            raise ValueError("输入影像少于 2 个波段，无法计算 NDVI。")

        # 读取 scale 和 offset
        scale, offset = get_scale_offset(src)

        print(f"Red band: {RED_BAND}")
        print(f"NIR band: {NIR_BAND}")
        print(f"Scale: {scale}")
        print(f"Offset: {offset}")
        print(f"Input nodata values: {src.nodatavals}")

        # 读取 Red 和 NIR 的 DN 值
        red_dn = src.read(RED_BAND).astype("float32")
        nir_dn = src.read(NIR_BAND).astype("float32")

        # 读取 nodata
        red_nodata = src.nodatavals[RED_BAND - 1]
        nir_nodata = src.nodatavals[NIR_BAND - 1]

        # 创建有效像素 mask
        # 一开始假设所有像素都有效
        valid_mask = np.ones(red_dn.shape, dtype=bool)

        # 如果 Red 是 nodata，则该像素无效
        if red_nodata is not None:
            valid_mask &= red_dn != red_nodata

        # 如果 NIR 是 nodata，则该像素无效
        if nir_nodata is not None:
            valid_mask &= nir_dn != nir_nodata

        # 把 DN 转为反射率
        # 这是这一步最关键的部分
        red = red_dn * scale + offset
        nir = nir_dn * scale + offset

        # NDVI 分母
        denominator = nir + red

        # 分母不能为 0，否则无法除法
        valid_mask &= denominator != 0

        # 创建 NDVI 数组
        # 默认全部填成 nodata
        ndvi = np.full(red.shape, OUTPUT_NODATA, dtype="float32")

        # 只对有效像素计算 NDVI
        ndvi[valid_mask] = (
            (nir[valid_mask] - red[valid_mask])
            / denominator[valid_mask]
        )

        # 防止极少数浮点误差导致超过 -1 到 1
        ndvi[valid_mask] = np.clip(ndvi[valid_mask], -1.0, 1.0)

        # 创建植被 mask
        # 0 = 非植被
        # 1 = 植被
        # 255 = nodata
        vegetation_mask = np.full(red.shape, 255, dtype="uint8")
        vegetation_mask[valid_mask & (ndvi < VEGETATION_THRESHOLD)] = 0
        vegetation_mask[valid_mask & (ndvi >= VEGETATION_THRESHOLD)] = 1

        # 准备 NDVI 输出文件的 profile
        ndvi_profile = src.profile.copy()
        ndvi_profile.update(
            {
                "count": 1,
                "dtype": "float32",
                "nodata": OUTPUT_NODATA,
                "compress": "lzw",
            }
        )

        # 准备 vegetation mask 输出文件的 profile
        mask_profile = src.profile.copy()
        mask_profile.update(
            {
                "count": 1,
                "dtype": "uint8",
                "nodata": 255,
                "compress": "lzw",
            }
        )

        # 写出 NDVI GeoTIFF
        with rasterio.open(NDVI_PATH, "w", **ndvi_profile) as dst:
            dst.write(ndvi, 1)
            dst.set_band_description(1, "NDVI")

        # 写出 vegetation mask GeoTIFF
        with rasterio.open(MASK_PATH, "w", **mask_profile) as dst:
            dst.write(vegetation_mask, 1)
            dst.set_band_description(1, "Vegetation Mask")

        # 统计像素数量
        total_pixel_count = int(red.size)
        valid_pixel_count = int(np.sum(valid_mask))
        nodata_pixel_count = int(total_pixel_count - valid_pixel_count)
        vegetation_pixel_count = int(np.sum(vegetation_mask[valid_mask] == 1))
        non_vegetation_pixel_count = int(np.sum(vegetation_mask[valid_mask] == 0))

        # 统计 NDVI 值
        if valid_pixel_count > 0:
            valid_ndvi_values = ndvi[valid_mask]

            stats = {
                "input_file": str(INPUT_PATH),
                "ndvi_file": str(NDVI_PATH),
                "vegetation_mask_file": str(MASK_PATH),
                "width": src.width,
                "height": src.height,
                "crs": str(src.crs),
                "red_band": RED_BAND,
                "nir_band": NIR_BAND,
                "input_nodata": red_nodata,
                "output_nodata": OUTPUT_NODATA,
                "mask_nodata": 255,
                "scale": scale,
                "offset": offset,
                "vegetation_threshold": VEGETATION_THRESHOLD,
                "ndvi_min": float(np.min(valid_ndvi_values)),
                "ndvi_max": float(np.max(valid_ndvi_values)),
                "ndvi_mean": float(np.mean(valid_ndvi_values)),
                "ndvi_std": float(np.std(valid_ndvi_values)),
                "total_pixel_count": total_pixel_count,
                "valid_pixel_count": valid_pixel_count,
                "nodata_pixel_count": nodata_pixel_count,
                "vegetation_pixel_count": vegetation_pixel_count,
                "non_vegetation_pixel_count": non_vegetation_pixel_count,
                "vegetation_ratio": float(vegetation_pixel_count / valid_pixel_count),
            }
        else:
            stats = {
                "input_file": str(INPUT_PATH),
                "ndvi_file": str(NDVI_PATH),
                "vegetation_mask_file": str(MASK_PATH),
                "width": src.width,
                "height": src.height,
                "crs": str(src.crs),
                "red_band": RED_BAND,
                "nir_band": NIR_BAND,
                "input_nodata": red_nodata,
                "output_nodata": OUTPUT_NODATA,
                "mask_nodata": 255,
                "scale": scale,
                "offset": offset,
                "vegetation_threshold": VEGETATION_THRESHOLD,
                "error": "No valid pixels found.",
            }

        # 写出 stats.json
        with open(STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print("\n=== Output Files ===")
        print(f"NDVI saved to: {NDVI_PATH}")
        print(f"Vegetation mask saved to: {MASK_PATH}")
        print(f"Stats saved to: {STATS_PATH}")

        print("\n=== Summary ===")
        print(f"Total pixels: {total_pixel_count}")
        print(f"Valid pixels: {valid_pixel_count}")
        print(f"NoData pixels: {nodata_pixel_count}")
        print(f"Vegetation pixels: {vegetation_pixel_count}")
        print(f"Non-vegetation pixels: {non_vegetation_pixel_count}")

        if valid_pixel_count > 0:
            print(f"NDVI min: {stats['ndvi_min']}")
            print(f"NDVI max: {stats['ndvi_max']}")
            print(f"NDVI mean: {stats['ndvi_mean']}")
            print(f"NDVI std: {stats['ndvi_std']}")
            print(f"Vegetation ratio: {stats['vegetation_ratio']}")

        print("\n=== NDVI Calculation Finished ===")


if __name__ == "__main__":
    main()