# 任务规格：卫星影像植被分析工具

## 目标

做一个面向遥感初学者 / 导师验收使用的卫星影像植被分析工具。
输入一景多波段 GeoTIFF 影像，输出 NDVI 栅格、植被掩膜与统计结果，用于判断植被分布和长势强弱。

## 输入

- 输入格式：GeoTIFF，文件名为 `data/input.tif`
- 输入影像需要包含 Red 波段和 NIR 波段
- Red / NIR 波段顺序通过影像元数据中的 `descriptions` 字段确认，不靠猜
- 数据类型以实际影像元数据为准，计算 NDVI 前需要转成浮点数
- nodata 以影像元数据为准
- 是否需要做 DN → 反射率转换，以影像 file tags 中的 `SCALE` / `OFFSET` 为准；若存在则必须先转换再算 NDVI

### 当前输入影像元数据

下面是使用 rasterio 读取 `input.tif` 得到的信息：

```text
file:        data/input.tif
width:       100
height:      100
count:       2
dtypes:      ('uint16', 'uint16')
nodata:      0.0
crs:         EPSG:32650
transform:   | 30.00, 0.00, 500000.00|
             | 0.00,-30.00, 4000000.00|
             | 0.00, 0.00, 1.00|
bounds:      BoundingBox(left=500000.0, bottom=3997000.0,
                          right=503000.0, top=4000000.0)
descriptions: ('Red', 'NIR')
scales:      (1.0, 1.0)
offsets:     (0.0, 0.0)
```

由 `descriptions: ('Red', 'NIR')` 确认：

```text
Band 1 = Red
Band 2 = NIR
```

文件级 tags 中含有：

```text
NOTE   = "reflectance = DN * SCALE + OFFSET; DN=0 is fill/nodata"
SCALE  = 2.75e-05
OFFSET = -0.2
```

因此本工具按以下方式处理像素值：

```text
reflectance = DN * 2.75e-05 + (-0.2)
NDVI        = (NIR_ref - Red_ref) / (NIR_ref + Red_ref)
DN = 0 视为 nodata，不参与 NDVI 计算
```

`rasterio` 的 `src.scales` / `src.offsets` 此处全为 1.0 / 0.0，不能用作转换系数；
真正的 SCALE / OFFSET 来自 `src.tags()`，代码中以此为准。

## 输出

所有输出写入 `outputs/` 目录。

| 文件                           | 内容                                                     | 类型 / nodata             |
| ------------------------------ | -------------------------------------------------------- | ------------------------- |
| `outputs/ndvi.tif`             | NDVI 栅格，1 波段                                        | float32 / `-9999.0`       |
| `outputs/vegetation_mask.tif`  | 植被掩膜：1 = 植被，0 = 非植被，255 = nodata             | uint8 / `255`             |
| `outputs/stats.json`           | 像素数、有效像素、植被像素、NDVI min/max/mean/std 等统计 | JSON                      |
| `outputs/ndvi_preview.png`     | NDVI 可视化预览图（彩色映射）                            | PNG                       |

输出栅格保留输入影像的 CRS（EPSG:32650）、transform、shape，确保可与输入在 GIS 中按地理坐标叠加。

## 约束

- 实现语言：Python ≥ 3.10
- 依赖库：`rasterio`、`numpy`、`matplotlib`（仅预览图使用）
- 入口命令：通过 `pyproject.toml` 暴露 `satveg` 命令，等价于 `python -m src.run_pipeline`
- 当前输入影像规模为 100 × 100，可整景一次性读入内存；若后续输入增大，需要改为按窗口分块读写（本版本不实现）

## 植被判断阈值

```text
NDVI >= 0.3  → vegetation = 1
NDVI <  0.3  → vegetation = 0
nodata 像素 → vegetation = 255
```

阈值 `0.3` 写在 `src/calculate_ndvi.py` 的 `VEGETATION_THRESHOLD` 常量中，便于后续调整。

## 验收标准（必须可执行）

1. 运行 `satveg` 命令成功结束，`outputs/` 目录下生成 `ndvi.tif`、`vegetation_mask.tif`、`stats.json`、`ndvi_preview.png` 四个文件。
2. `ndvi.tif` 元数据满足：`dtype = float32`、`nodata = -9999.0`、`count = 1`、CRS / transform / shape 与 `input.tif` 完全一致。
3. `ndvi.tif` 中所有有效像素（非 nodata）的值落在 `[-1, 1]`。
4. 任取 3 个有效像素，按 `NDVI = (NIR_ref - Red_ref) / (NIR_ref + Red_ref)` 手算，与文件中同位置值的 `abs diff < 1e-5`。
5. `vegetation_mask.tif` 像素值集合为 `{0, 1, 255}`，且 `0 + 1` 之和等于 `stats.json` 中的 `valid_pixel_count`。
6. `stats.json` 中 `valid_pixel_count + nodata_pixel_count == width * height`。

上述 1–6 项分别由 `checks/check_outputs.py`、`checks/validate_ndvi.py`、`checks/manual_pixel_check.py` 自动检查；运行结果记录在 `VALIDATION.md`。

## 非目标（明确不做）

- 不做大气校正、几何校正、辐射定标等任何上游遥感预处理，假设输入已是导师提供的可直接转反射率的 DN。
- 不支持除 GeoTIFF 以外的输入格式（HDF / NetCDF / Sentinel SAFE 等不在范围）。
- 不实现分块 / 流式读取，输入需可整景读入内存。
- 不做时序分析（单景 NDVI，不计算 NDVI 时间序列差异）。
- 不做植被分类（只做二值植被 / 非植被掩膜，不区分树木 / 草地 / 农田等）。
- 不内置交互式 Web 界面，只提供 CLI。
