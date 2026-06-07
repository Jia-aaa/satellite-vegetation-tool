# 📦 交付清单

> 本文件唯一目的：**让导师 30 秒内对上任务要的东西在哪。**

---

## 任务原文（TASK_1.md）

**第 3 节 — 工具最终需要输出三个文件：**

1. `outputs/ndvi.tif`：NDVI 结果图
2. `outputs/vegetation_mask.tif`：植被掩膜图
3. `outputs/stats.json`：统计结果

**第 5 节 — 验收标准（5 条）：**

1. 手算几个像素的 NDVI，和程序结果对比
2. 有效 NDVI 应该在 -1 到 1 之间
3. nodata 像素不能参与计算
4. 输出影像要和输入影像地理位置对齐
5. 用 QGIS 或其他软件叠图检查结果是否合理

---

## 1. 三个产物文件 → `outputs/`

| 任务要的文件 | 路径 | 说明 |
|---|---|---|
| NDVI 结果图 | [`outputs/ndvi.tif`](outputs/) | float32，nodata = `-9999.0`，CRS / transform / shape 与输入一致 |
| 植被掩膜 | [`outputs/vegetation_mask.tif`](outputs/) | uint8，`1=植被 / 0=非植被 / 255=nodata`，阈值 `NDVI ≥ 0.3` |
| 统计结果 | [`outputs/stats.json`](outputs/) | 像素计数 / NDVI min/max/mean/std / 植被比例 |

附加产物（不在任务点名清单内，方便检查）：

- `outputs/ndvi_preview.png` — NDVI 彩色预览图

复现方式：

```bash
pip install -e .
satveg
```

## 2. 工具代码 → [`src/`](src/)

| 模块 | 路径 | 说明 |
|---|---|---|
| 主流水线 | [`src/run_pipeline.py`](src/run_pipeline.py) | `satveg` 命令入口，依次跑 NDVI → 掩膜 → 预览 → 自检 |
| NDVI / 掩膜 / 统计 | [`src/calculate_ndvi.py`](src/calculate_ndvi.py) | 核心计算（含 `VEGETATION_THRESHOLD = 0.3`） |
| 预览图 | [`src/visualize_ndvi.py`](src/visualize_ndvi.py) | 生成 `ndvi_preview.png` |
| 输入元数据 | [`src/check_raster_info.py`](src/check_raster_info.py) | 辅助：打印 input.tif 元数据 |

## 3. 规格 → [`SPEC.md`](SPEC.md)

包含：目标、输入波段确认、NDVI 公式与 scale/offset 处理、植被阈值、输出规格、5 条验收标准、非目标。

## 4. 验收报告 → [`VALIDATION.md`](VALIDATION.md)

5 条任务验收标准在报告中的位置：

| 任务验收 | 在 VALIDATION.md 的位置 | 对应自检脚本 |
|---|---|---|
| 1. 手算像素 NDVI 对拍 | [§5 手算验证](VALIDATION.md) | [`checks/manual_pixel_check.py`](checks/manual_pixel_check.py) |
| 2. NDVI 范围 ∈ [-1, 1] | [§6 范围检查](VALIDATION.md) | [`checks/validate_ndvi.py`](checks/validate_ndvi.py) + [`checks/check_outputs.py`](checks/check_outputs.py) |
| 3. nodata 不参与计算 | [§4 自动验收检查](VALIDATION.md) + [§8 边界情况](VALIDATION.md) | [`checks/check_outputs.py`](checks/check_outputs.py) |
| 4. 输出与输入地理对齐 | [§7 地理参考检查](VALIDATION.md) | [`checks/check_outputs.py`](checks/check_outputs.py) + [`checks/validate_ndvi.py`](checks/validate_ndvi.py) |
| 5. QGIS 叠图合理 | [§9 QGIS 叠图检查](VALIDATION.md) | 人工，截图见 §9 |

3 个独立自检脚本可单独运行：

```bash
python checks/check_outputs.py        # 输出元数据 / 范围 / mask&stats 一致性
python checks/validate_ndvi.py        # 独立重读 NDVI，做范围 + 地理参考检查
python checks/manual_pixel_check.py   # 任取 3 个有效像素手算对拍
```

---

## 📂 一图看懂仓库结构

```
satellite-vegetation-tool/
│
├── DELIVERABLES.md          ← 你正在看的这份（交付索引）
├── TASK_1.md                ← 任务原文
├── SPEC.md                  ← 【交付】规格
├── VALIDATION.md            ← 【交付】验收报告（对照任务 5 条验收标准）
├── README.md
├── pyproject.toml           暴露 satveg 命令
├── requirements.txt
│
├── src/                     ← 【交付】工具代码
│   ├── run_pipeline.py
│   ├── calculate_ndvi.py
│   ├── visualize_ndvi.py
│   └── check_raster_info.py
│
├── checks/                  独立自检脚本
│   ├── check_outputs.py
│   ├── validate_ndvi.py
│   └── manual_pixel_check.py
│
├── data/                    （不入库：input.tif）
└── outputs/                 ← 【交付】3 个产物文件
    ├── ndvi.tif                  任务点名 #1
    ├── vegetation_mask.tif       任务点名 #2
    ├── stats.json                任务点名 #3
    └── ndvi_preview.png          附加：彩色预览图
```
