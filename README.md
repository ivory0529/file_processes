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

## 安装流程

### 1. Dify 工作流结果自动导出到本地目录

本项目可通过 Dify 工作流 + 自定义代码节点，将生成的内容（如 OCR 或结构化数据）**自动导出到本地磁盘目录**，便于下载、分析和后续处理。  
实现方式是：在 Dify 的 sandbox 容器与宿主机之间做 volume 映射，实现工作流内保存的文件实时同步到本地。

---

### 步骤一：准备 Sandbox 目录（容器 + 本地）

#### 1.1 进入 sandbox 容器，创建导出目录

```bash
# 进入 Dify sandbox 容器（容器名以实际为准，通常是 docker-sandbox-1）
docker exec -it docker-sandbox-1 bash

# 切换到临时目录
cd /var/sandbox/sandbox-python/tmp/

# 创建用于导出的文件夹
mkdir file

# 推荐给予全目录写权限
chmod -R 777 /var/sandbox/sandbox-python/tmp/
```

### 1.2 在本地机器创建挂载目录

```python
cd /dify/docker/volumes/sandbox/
mkdir file
chmod -R 777 file
```

### 步骤二: 配置 Docker 映射

编辑 docker-compose.yaml，在 sandbox 节点下的 volumes: 增加如下内容：

```bash
cd /dify/docker/volumes/sandbox/
mkdir file
chmod -R 777 file
```

完成后重启 Dify 服务

### 步骤三：Dify 工作流内自定义导出代码

在 Dify 工作流中，插入一个 Python 代码节点，参考如下代码：

```python
import os
import json

def main(arg1: list, user_id: str) -> dict:
    # 文件将导出到容器映射目录
    file_path = f'/tmp/file/{user_id}_response.json'
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    json_str = json.dumps(arg1, ensure_ascii=False, indent=4)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
    return {
        "result": f'文件生成完毕：{file_path}'
    }

```

运行 Dify 工作流后，可在本地 ./volumes/sandbox/file/ 目录直接找到对应的输出文件，如 user_xxx_response.json 或 .txt。

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


