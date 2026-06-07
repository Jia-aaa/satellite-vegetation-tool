# 自检报告：卫星影像植被分析工具

## 1. 运行检查

运行命令：

```bash
satveg
```

结果：工具可以正常运行，并在 `outputs/` 目录下生成 `ndvi.tif`、`vegetation_mask.tif`、`stats.json`、`ndvi_preview.png`。

`satveg` 完整输出（节选关键部分）：

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

通过 rasterio 读取 `data/input.tif` 元数据，确认输入影像共有 2 个波段：

```text
count: 2
descriptions: ('Red', 'NIR')
dtypes: ('uint16', 'uint16')
nodata: 0.0
crs: EPSG:32650
```

文件 tags 中存有：

```text
SCALE  = 2.75e-05
OFFSET = -0.2
```

因此本工具计算 NDVI 时使用：

```text
Red band = 1
NIR band = 2
```

## 3. NDVI 公式

DN 通过 `SCALE` / `OFFSET` 转为反射率，再按标准 NDVI 公式计算：

```text
reflectance = DN * SCALE + OFFSET
NDVI        = (NIR_ref - Red_ref) / (NIR_ref + Red_ref)
```

DN 在计算前转成 `float32`，避免整数除法。

## 4. 自动自检结果

运行 `python checks/validate_ndvi.py`，独立用 rasterio 重新读输入和输出文件后输出：

```text
=== Validation report ===

input file      : data\input.tif
input shape     : (100, 100)
input crs       : EPSG:32650
input transform : | 30.00, 0.00, 500000.00|
| 0.00,-30.00, 4000000.00|
| 0.00, 0.00, 1.00|

ndvi file       : outputs\ndvi.tif
ndvi shape      : (100, 100)
ndvi crs        : EPSG:32650
ndvi transform  : | 30.00, 0.00, 500000.00|
| 0.00,-30.00, 4000000.00|
| 0.00, 0.00, 1.00|
ndvi nodata     : -9999.0

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

运行 `python checks/manual_pixel_check.py`，从 `input.tif` 直接读 3 个有效像素的 DN，按公式手算 NDVI，再与 `outputs/ndvi.tif` 同位置的值比较。

验收标准：`abs(manual_ndvi - code_ndvi)` 应接近 0，只允许浮点误差。

实际输出：

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

3 个像素的手算结果与代码输出最大差 `7.53e-08`，属于 `float32` 计算的正常浮点误差，公式与波段顺序均正确。

## 6. 范围检查

NDVI 理论有效范围为 `[-1, 1]`。

实际有效像素的 NDVI：

```text
ndvi min : -0.39983001351356506
ndvi max :  0.8589791059494019
```

均在 `[-1, 1]` 内，验证脚本输出 `range ok`。

## 7. 地理参考检查

验证脚本对 `input.tif` 与 `outputs/ndvi.tif` 比较了：

```text
crs match       : True
transform match : True
shape match     : True
```

三项均一致，输出 NDVI 完整保留了原始影像的地理参考信息（CRS = EPSG:32650，30 米像元，左上角 500000.0, 4000000.0）。

## 8. 边界情况说明

代码中已处理以下边界情况（见 `src/calculate_ndvi.py`）：

- **输入 nodata（0.0）**：通过 `valid_mask &= red_dn != red_nodata` 与 NIR 同样处理，参与 NDVI 计算前剔除。
- **NIR + Red = 0（除零）**：在反射率域计算分母后用 `valid_mask &= denominator != 0` 剔除，避免除零。
- **无效像素输出**：NDVI 输出文件用 `-9999.0` 作为 nodata 填充，植被掩膜用 `255` 作为 nodata。
- **浮点越界保护**：对有效像素的 NDVI 做 `np.clip(-1, 1)`，防止极端浮点误差产生 `|NDVI| > 1` 的值。
- **输出统计**：`stats.json` 中 `valid_pixel_count = 8100`，`nodata_pixel_count = 1900`，合计 10000，与影像总像素数一致。

## 9. QGIS 叠图检查

已在 QGIS 中同时打开 `data/input.tif` 与 `outputs/ndvi.tif`，两者在地图上完全对齐，bounds、像元大小一致，未出现错位或偏移。NDVI 高值区域与原影像中肉眼可识别的植被区域吻合，说明输出栅格保留了正确的地理参考，植被分布在空间上合理。
