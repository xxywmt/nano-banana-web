# 科研示意图生成器

基于 Nano Banana API 的科研示意图在线生成工具。

## 功能特点

- 文字描述生成科研示意图
- 支持上传参考图
- 多种模型和分辨率选择
- 在线预览和下载

## 使用方法

1. 输入 API Key
2. 描述你想要的示意图
3. 选择模型、比例和分辨率
4. 点击生成

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 环境变量

可选：设置 `NANO_BANANA_API_KEY` 环境变量以避免每次输入
