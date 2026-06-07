# 卫星影像植被分析工具

从一景双波段卫星 GeoTIFF 影像计算 NDVI、生成植被掩膜与统计信息的命令行工具。

---

## 📦 交付清单（任务一第 3 节 + 第 5 节）

> 任务原文（第 3 节）："工具最终需要输出三个文件：`outputs/ndvi.tif` / `outputs/vegetation_mask.tif` / `outputs/stats.json`。"
> 任务原文（第 5 节验收）：手算像素对拍、NDVI ∈ [-1, 1]、nodata 不参与计算、输出与输入地理对齐、QGIS 叠图合理。

| # | 任务要的东西 | 在仓库里的位置 |
|---|---|---|
| 1 | **`outputs/ndvi.tif`** —— NDVI 结果图 | 由 `satveg` 生成；规格见 [`SPEC.md`](SPEC.md) |
| 2 | **`outputs/vegetation_mask.tif`** —— 植被掩膜 | 由 `satveg` 生成；阈值 `NDVI ≥ 0.3`（`src/calculate_ndvi.py`） |
| 3 | **`outputs/stats.json`** —— 统计结果 | 由 `satveg` 生成；含像素计数 / NDVI min/max/mean/std / 植被比例 |
| 4 | **工具代码** | [`src/`](src/) —— 入口 `src/run_pipeline.py`（`satveg` 命令） |
| 5 | **规格** | [`SPEC.md`](SPEC.md) |
| 6 | **验收报告**（5 条验收标准的逐项证明） | [`VALIDATION.md`](VALIDATION.md) + [`checks/`](checks/) 三个独立脚本 |

补充材料：

- `outputs/ndvi_preview.png` —— NDVI 彩色预览图（方便不开 GIS 也能直观看）
- [`checks/manual_pixel_check.py`](checks/manual_pixel_check.py) —— 任务第 5.1 条"手算像素对拍"的实证脚本
- [`checks/validate_ndvi.py`](checks/validate_ndvi.py) —— 独立重读 NDVI，验证 [-1, 1] 与地理参考

---

## 功能

输入 `data/input.tif`（双波段，Band 1 = Red，Band 2 = NIR），输出到 `outputs/`：

| 文件                          | 内容                                                | 类型 / nodata        |
| ----------------------------- | --------------------------------------------------- | -------------------- |
| `outputs/ndvi.tif`            | NDVI 栅格                                           | float32 / `-9999.0`  |
| `outputs/vegetation_mask.tif` | 植被掩膜：1 = 植被，0 = 非植被，255 = nodata        | uint8 / `255`        |
| `outputs/stats.json`          | 像素计数、NDVI min/max/mean/std、植被比例等统计     | JSON                 |
| `outputs/ndvi_preview.png`    | NDVI 彩色预览图                                     | PNG                  |

NDVI 计算流程：

```text
reflectance = DN * SCALE + OFFSET   (SCALE/OFFSET 来自 input.tif 的 file tags)
NDVI        = (NIR_ref - Red_ref) / (NIR_ref + Red_ref)
DN = 0 视为 nodata，不参与计算
NDVI ≥ 0.3 判为植被
```

输出栅格保留输入影像的 CRS、transform、shape，可在 GIS 中按地理坐标与原影像叠加。

## 安装

需要 Python 3.10 及以上。

```bash
pip install -e .
```

或者：

```bash
pip install -r requirements.txt
```

## 运行

把待处理影像放在 `data/input.tif`，然后在项目根目录执行：

```bash
satveg
```

流水线依次执行：计算 NDVI 和植被掩膜 → 生成预览图 → 自动验收检查。任一步失败会以非零退出码终止，并打印失败原因。

植被阈值默认为 `0.3`，定义在 `src/calculate_ndvi.py` 的 `VEGETATION_THRESHOLD`。如需调整改这个常量即可。

## 验证

`checks/` 目录下有三个独立验证脚本，可单独运行：

```bash
python checks/check_outputs.py        # 输出元数据 / 范围 / mask & stats 一致性
python checks/validate_ndvi.py        # 独立重读 NDVI 文件，做范围 + 地理参考检查
python checks/manual_pixel_check.py   # 任取 3 个有效像素手算对拍
```

完整的自检结果记录在 [`VALIDATION.md`](VALIDATION.md)。规格说明见 [`SPEC.md`](SPEC.md)。

## 项目结构

```
satellite-vegetation-tool/
├── SPEC.md                          规格
├── VALIDATION.md                    自检报告
├── README.md
├── pyproject.toml                   暴露 satveg 命令
├── requirements.txt
├── data/input.tif                   输入影像（不入库）
├── outputs/                         运行产物（不入库）
├── src/
│   ├── run_pipeline.py              satveg 入口
│   ├── calculate_ndvi.py            NDVI / 掩膜 / 统计
│   ├── visualize_ndvi.py            预览图
│   └── check_raster_info.py         辅助：打印输入元数据
└── checks/
    ├── check_outputs.py             输出验收（被 satveg 调用）
    ├── validate_ndvi.py             独立对拍：范围 + 地理参考
    └── manual_pixel_check.py        独立对拍：3 像素手算
```
