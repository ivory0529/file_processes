import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ================================ 配置区域 ================================
class Config:
    # API配置
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    DIFY_API_KEY = os.getenv("DIFY_API_KEY")
    DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://localhost")
    ENABLE_DIFY = os.getenv("ENABLE_DIFY", "false").lower() == "true"

    # 路径配置
    MD_OUT_DIR = Path(os.getenv("MD_OUT_DIR", "./output/markdown"))
    IMAGE_DIR = Path(os.getenv("IMAGE_DIR", "./output/images"))
    EXCEL_PATH = Path(os.getenv("EXCEL_PATH", "./output/pdf_processing.xlsx"))
    DIFY_RESULT_DIR = Path(os.getenv("DIFY_RESULT_DIR", "./output/dify_results"))

    # 处理配置
    MODEL_NAME = "mistral-ocr-latest"
    MAX_WORKERS = 3
    DIFY_MAX_WORKERS = 2
