# VOC Data Product

母婴跨境电商本地化 VOC 舆情分析数据产品。

## 覆盖范围

- **40 个国家** × **10 条产品品线**
- TOP20 重点国家深挖，TOP10 平台入口打法
- 用户画像、购买力分析、信息源分层

## 快速启动

```bash
# 1. 生成数据
cd tools && python export_viz_json.py

# 2. 启动后端
cd app/dashboard/backend && python -m uvicorn main:app --port 8000

# 3. 启动前端
cd app/dashboard/frontend && npm install && npm run dev

# 4. (可选) 独立交付站
cd viz-static && npm install && npm run dev
```

## 项目结构

详见 [docs/00_项目导航.md](docs/00_项目导航.md)。
