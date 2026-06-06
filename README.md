\# Satellite Vegetation Tool



一个用于处理卫星影像并计算 NDVI（归一化植被指数）的 Python 小工具。



\## 功能



目前支持：



\- 读取红光波段和近红外波段影像

\- 计算 NDVI

\- 输出 NDVI GeoTIFF 文件

\- 生成 NDVI 彩色预览图 PNG



\## 项目结构



```text

satellite-vegetation-tool/

├── data/                  # 输入影像数据

├── output/                # 输出结果，不提交到 Git

├── src/

│   ├── calculate\_ndvi.py  # 计算 NDVI

│   └── visualize\_ndvi.py  # 生成 NDVI 预览图

├── requirements.txt       # Python 依赖

├── .gitignore

└── README.md

