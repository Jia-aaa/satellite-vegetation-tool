# 自检报告：卫星影像植被分析工具

本报告对应 `SPEC.md` 中的验收标准 1–6，以及任务文档要求的额外人工检查项。
所有自动检查由 `checks/` 目录下的脚本完成，可独立复跑。

| 验收编号 | 自动脚本                          | 内容                               |
| -------- | --------------------------------- | ---------------------------------- |
| 1        | `checks/check_outputs.py`         | 四个输出文件存在                   |
| 2        | `checks/check_outputs.py`         | NDVI dtype/nodata/count/CRS/transform/shape |
| 3        | `checks/check_outputs.py` + `checks/validate_ndvi.py` | NDVI 落在 [-1, 1] |
| 4        | `checks/manual_pixel_check.py`    | 3 像素手算对拍                     |
| 5        | `checks/check_outputs.py`         | mask 取值 ⊂ {0,1,255}，0+1 = valid |
| 6        | `checks/check_outputs.py`         | valid + nodata = width × height    |

## 1. 运行检查

入口命令：

```bash
satveg
```

流水线 `Pipeline completed successfully.` 正常结束，`outputs/` 下生成：

```text
outputs/ndvi.tif
outputs/vegetation_mask.tif
outputs/stats.json
outputs/ndvi_preview.png
```

`satveg` 关键输出：

```text
=== NDVI Calculation Started ===
Input file: data\input.tif
Red band: 1
NIR band: 2
Scale: 2.75e-05
Offset: -0.2
Input nodata values: (0.0, 0.0)

=== Summary ===
Total pixels: 10000
Valid pixels: 8100
NoData pixels: 1900
Vegetation pixels: 1600
Non-vegetation pixels: 6500
NDVI min: -0.39983001351356506
NDVI max: 0.8589791059494019
NDVI mean: 0.21008731424808502
NDVI std: 0.32271283864974976
Vegetation ratio: 0.19753086419753085
```

## 2. 输入波段确认

通过 rasterio 读取 `data/input.tif` 元数据：

```text
count: 2
descriptions: ('Red', 'NIR')
dtypes: ('uint16', 'uint16')
nodata: 0.0
crs: EPSG:32650
```

文件 file tags：

```text
NOTE   = "reflectance = DN * SCALE + OFFSET; DN=0 is fill/nodata"
SCALE  = 2.75e-05
OFFSET = -0.2
```

由 `descriptions` 字段确认：

```text
Band 1 = Red
Band 2 = NIR
```

## 3. NDVI 公式

DN 通过 `SCALE` / `OFFSET` 转为反射率，再按标准 NDVI 公式计算：

```text
reflectance = DN * SCALE + OFFSET
NDVI        = (NIR_ref - Red_ref) / (NIR_ref + Red_ref)
```

DN 在计算前转成 `float32`，避免整数除法。计算后对有效像素 `np.clip(-1, 1)`，
防止极端浮点误差产生 `|NDVI| > 1`。

## 4. 自动验收检查

运行 `python checks/check_outputs.py`，全部 PASS：

```text
################################
Output acceptance checks
################################
input crs       : EPSG:32650
input transform : | 30.00, 0.00, 500000.00|
| 0.00,-30.00, 4000000.00|
| 0.00, 0.00, 1.00|
input shape     : (100, 100)

=== File existence ===
OK: outputs\ndvi.tif exists
OK: outputs\vegetation_mask.tif exists
OK: outputs\stats.json exists
OK: outputs\ndvi_preview.png exists

=== NDVI raster ===
OK: driver is GTiff
OK: band count is 1
OK: dtype is float32
OK: nodata is -9999.0
OK: CRS matches input (EPSG:32650)
OK: transform matches input
OK: shape matches input (100, 100)
OK: valid NDVI in [-1, 1]  (min=-0.399830, max=0.858979)

=== Vegetation mask ===
OK: dtype is uint8
OK: nodata is 255
OK: CRS matches input (EPSG:32650)
OK: transform matches input
OK: shape matches input (100, 100)
OK: mask values subset of {0,1,255}: [0, 1, 255]

=== Stats / mask consistency ===
OK: mask 0+1 (8100) == stats.valid_pixel_count (8100)
OK: valid+nodata (10000) == width*height (10000)
OK: mask 255 count (1900) == stats.nodata_pixel_count (1900)

=== Summary ===
All output acceptance checks passed.
```

`check_outputs.py` 不再硬编码 `EPSG:32650` / `100x100`，而是动态读取
`data/input.tif` 的 CRS / transform / shape 与输出对比，换一景影像也能直接验收。

补充验证：运行 `python checks/validate_ndvi.py`：

```text
=== Range check ===
valid pixels : 8100
ndvi min     : -0.39983001351356506
ndvi max     : 0.8589791059494019
range ok: NDVI in [-1, 1]

=== Geo reference check ===
crs match       : True
transform match : True
shape match     : True
geo ref ok
```

## 5. 手算验证

运行 `python checks/manual_pixel_check.py`：从 `input.tif` 直接读 3 个有效像素的 DN，
按公式手算 NDVI，与 `outputs/ndvi.tif` 同位置值比较。

验收标准：`abs(manual_ndvi - code_ndvi) < 1e-5`。

```text
=== Manual pixel check ===
scale = 2.75e-05
offset = -0.2
red_nodata = 0.0, nir_nodata = 0.0
ndvi_nodata = -9999.0
total valid pixels = 8100

Pixel 1: row=5, col=5
  Red DN  = 14348.0
  NIR DN  = 16627.0
  Red ref = 0.19457000
  NIR ref = 0.25724250
  manual NDVI = 0.13871352
  code   NDVI = 0.13871354
  abs diff    = 2.36e-08

Pixel 2: row=50, col=5
  Red DN  = 13967.0
  NIR DN  = 16465.0
  Red ref = 0.18409250
  NIR ref = 0.25278750
  manual NDVI = 0.15723997
  code   NDVI = 0.15723990
  abs diff    = 7.53e-08

Pixel 3: row=94, col=94
  Red DN  = 13933.0
  NIR DN  = 16084.0
  Red ref = 0.18315750
  NIR ref = 0.24231000
  manual NDVI = 0.13902942
  code   NDVI = 0.13902946
  abs diff    = 3.76e-08

Max abs diff over 3 pixels: 7.53e-08
RESULT: OK (within float tolerance)
```

3 个像素的最大差 `7.53e-08`，远小于 `1e-5` 的验收门限，公式与波段顺序均正确。

## 6. 范围检查

NDVI 理论有效范围 `[-1, 1]`。实际有效像素：

```text
ndvi min : -0.39983001351356506
ndvi max :  0.8589791059494019
```

均落在 `[-1, 1]` 内（`check_outputs.py` 与 `validate_ndvi.py` 双重确认）。

## 7. 地理参考检查

`check_outputs.py` 与 `validate_ndvi.py` 都对 `data/input.tif` 与 `outputs/ndvi.tif`、
`outputs/vegetation_mask.tif` 比较了 CRS / transform / shape：

```text
crs match       : True
transform match : True
shape match     : True
```

输出栅格完整保留了输入影像的地理参考（EPSG:32650，30 米像元，左上角 500000.0 / 4000000.0）。

## 8. 边界情况说明

代码在 `src/calculate_ndvi.py` 中处理了以下边界情况：

- **输入 nodata（0.0）**：`valid_mask &= red_dn != red_nodata` 与 NIR 同样处理，
  在 NDVI 计算前剔除。
- **NIR + Red = 0（除零）**：在反射率域计算分母后用 `valid_mask &= denominator != 0` 剔除。
- **无效像素输出**：NDVI 用 `-9999.0` 作为 nodata，植被掩膜用 `255`。
- **浮点越界保护**：对有效 NDVI 做 `np.clip(-1, 1)`，防止 float32 误差超界。
- **像素计数一致**：`stats.json` 中 `valid_pixel_count + nodata_pixel_count` 严格等于 `width * height`，
  且 `vegetation_pixel_count + non_vegetation_pixel_count == valid_pixel_count`，由验收脚本断言。

## 9. QGIS 叠图检查

已在 QGIS 中同时打开 `data/input.tif` 与 `outputs/ndvi.tif`，两者在地图上完全对齐，
bounds、像元大小一致，未出现错位或偏移。NDVI 高值区域与原影像中肉眼可识别的植被区域吻合，
说明输出栅格保留了正确的地理参考，植被分布在空间上合理。

## 复现方法

```bash
pip install -e .
satveg                                  # 完整流水线 + 验收
python checks/check_outputs.py          # 单独跑验收
python checks/validate_ndvi.py          # 范围 + 地理参考
python checks/manual_pixel_check.py     # 3 像素手算
```

任一脚本失败会以非零退出码终止。
