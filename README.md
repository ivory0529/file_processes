# PDF批量OCR处理与Dify增强工具

## 简介

本工具支持 **批量PDF文件的OCR识别**、**图片与文本提取**、**自动生成Markdown**、**可选上传Dify工作流增强处理**，**所有处理结果自动记录到Excel表**，并配有**可视化操作界面（Tkinter）**，操作简便，一键完成全流程。

- 支持 OCR+图片批量抽取
- 支持 Markdown 文件输出
- 支持 Dify 工作流自动上传和结果监控（可选）
- 处理日志、结果记录自动存入 Excel
- 界面友好，适合非技术用户批量处理文档

---

## 功能特点

- 多文件批量处理
- 一键OCR（Mistral OCR API）
- 可选 Dify 流程增强
- 处理结果自动存 Markdown/图片/Excel
- 操作全过程有进度条和状态显示
- 日志和结果目录一键打开

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 .env

在项目根目录下创建 .env 文件，内容示例：
```python
MISTRAL_API_KEY=your-mistral-api-key
DIFY_API_KEY=your-dify-api-key  # 可选
DIFY_BASE_URL=http://localhost  # Dify服务地址
MD_OUT_DIR=./output/markdown
IMAGE_DIR=./output/images
EXCEL_PATH=./output/pdf_processing.xlsx
DIFY_RESULT_DIR=./output/dify_results
ENABLE_DIFY=false
```

### 3. 启动程序
```python
python main.py
```

### 4. 文件结构

- main.py 程序入口
- gui.py 可视化界面
- ocr_processor.py OCR与图片/markdown处理
- dify_processor.py Dify相关处理
- tracker.py Excel追踪/记录
- config.py 配置加载
- utils.py 工具函数
- output/ 处理结果（markdown、图片、excel、dify结果）


