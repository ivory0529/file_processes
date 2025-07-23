# dify_processor.py

import time
from pathlib import Path
from config import Config
import requests
from datetime import datetime
import logging
from typing import Optional

class DifyProcessor:
    def __init__(self, tracker):
        self.tracker = tracker
        self.logger = logging.getLogger(f"{__name__}.DifyProcessor")
        self.api_key = Config.DIFY_API_KEY
        self.base_url = Config.DIFY_BASE_URL.rstrip('/')

        if not self.api_key:
            self.logger.warning("⚠️ 未设置DIFY_API_KEY，Dify功能将被禁用")

    def process_markdown(self, md_path: Path, user_id: str = "batch_user") -> dict:
        if not self.api_key:
            return {"success": False, "error": "Dify API未配置"}

        pdf_name = md_path.stem
        self.tracker.update_record(pdf_name, dify_status="正在上传...")

        try:
            self.logger.info(f"📤 上传文件到Dify: {md_path.name}")
            file_id = self._upload_file(md_path, user_id)
            if not file_id:
                return {"success": False, "error": "文件上传失败"}

            self.tracker.update_record(pdf_name, dify_file_id=file_id, dify_status="正在处理...")

            self.logger.info(f"🔄 运行Dify工作流，文件ID: {file_id}")
            result = self._run_workflow(file_id, user_id)

            if result.get("success"):
                self.logger.info(f"🔍 等待TXT文本生成节点创建结果文件...")
                time.sleep(5)
                result_file = self._check_result_file(pdf_name, user_id, max_wait=120)
                if result_file:
                    status = "✅完成"
                    dify_result = "✅"
                    self.logger.info(f"🎉 Dify处理完成: {result_file.name}")
                else:
                    status = "⚠️工作流成功但未找到结果文件"
                    dify_result = "⚠️"
                    self.logger.warning(f"⚠️ 工作流执行成功但未找到结果文件")
                self.tracker.update_record(
                    pdf_name,
                    dify_status=status,
                    dify_result=dify_result
                )
                return {
                    "success": True,
                    "file_id": file_id,
                    "result_file": result_file,
                    "workflow_result": result,
                    "found_result_file": bool(result_file)
                }
            else:
                self.tracker.update_record(pdf_name, dify_status="❌失败", dify_result="❌")
                return result

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"💥 Dify处理失败 {pdf_name}: {error_msg}")
            self.tracker.update_record(pdf_name, dify_status="❌错误", dify_result="❌")
            return {"success": False, "error": error_msg}

    def _upload_file(self, file_path: Path, user_id: str):
        upload_url = f"{self.base_url}/v1/files/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            with open(file_path, 'rb') as file:
                files = {
                    'file': (file_path.name, file, 'text/markdown')
                }
                data = {
                    "user": user_id,
                    "type": "document"
                }
                response = requests.post(upload_url, headers=headers, files=files, data=data, timeout=30)
                if response.status_code == 201:
                    result = response.json()
                    file_id = result.get("id")
                    self.logger.info(f"✅ 文件上传成功: {file_id}")
                    return file_id
                else:
                    self.logger.error(f"❌ 文件上传失败，状态码: {response.status_code}")
                    self.logger.error(f"响应内容: {response.text}")
                    return None
        except requests.exceptions.Timeout:
            self.logger.error("文件上传超时")
            return None
        except Exception as e:
            self.logger.error(f"上传过程异常: {str(e)}")
            return None

    def _run_workflow(self, file_id: str, user_id: str, response_mode: str = "blocking") -> dict:
        workflow_url = f"{self.base_url}/v1/workflows/run"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": {
                "file": {
                    "transfer_method": "local_file",
                    "upload_file_id": file_id,
                    "type": "document"
                }
            },
            "response_mode": response_mode,
            "user": user_id
        }
        try:
            self.logger.info(f"🔄 发送工作流请求")
            self.logger.info(f"📤 请求数据: {data}")

            response = requests.post(workflow_url, headers=headers, json=data, timeout=300)
            self.logger.info(f"📥 响应状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"✅ 工作流执行成功")
                self.logger.info(f"📋 工作流结果: {result}")
                return {"success": True, "result": result}
            else:
                self.logger.error(f"❌ 工作流执行失败，状态码: {response.status_code}")
                self.logger.error(f"📄 响应内容: {response.text}")
                return {"success": False, "error": f"工作流失败: {response.status_code}"}
        except Exception as e:
            self.logger.error(f"💥 工作流执行异常: {str(e)}")
            return {"success": False, "error": str(e)}

    def _check_result_file(self, pdf_name: str, user_id: str, max_wait: int = 120) -> Optional[Path]:
        """
        检查Dify结果目录是否生成了txt结果文件。
        只匹配pattern，不判断生成时间，只取mtime最新的文件返回。
        """
        self.logger.info(f"🔍 检查Dify结果文件（不判断时间）...")
        possible_patterns = [
            f"user_{pdf_name}_response*.txt",
            f"user_*{pdf_name}*.txt",
            f"*{pdf_name}*response*.txt",
            "*response*.txt",
            f"{user_id}_response*.txt"
        ]
        for wait_count in range(max_wait):
            found = []
            for pattern in possible_patterns:
                for f in Config.DIFY_RESULT_DIR.glob(pattern):
                    if f.is_file():
                        found.append(f)
            if found:
                newest_file = max(found, key=lambda f: f.stat().st_mtime)
                mtime = datetime.fromtimestamp(newest_file.stat().st_mtime)
                self.logger.info(f"✅ 找到txt文件: {newest_file.name}（生成时间: {mtime}）")
                return newest_file
            if wait_count % 10 == 0 and wait_count > 0:
                self.logger.info(f"⏳ 等待中... ({wait_count}s)")
                self.logger.info(f"🔍 查找模式: {possible_patterns[:3]}")
                all_files = sorted(Config.DIFY_RESULT_DIR.glob("*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)[:5]
                for rf in all_files:
                    rf_mtime = datetime.fromtimestamp(rf.stat().st_mtime)
                    self.logger.info(f"   {rf.name} ({rf_mtime})")
            time.sleep(1)
        self.logger.warning("❌ 等待超时也没找到任何txt文件")
        return None
