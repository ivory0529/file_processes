# tracker.py
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime

class ProcessingTracker:
    def __init__(self, excel_path: Path):
        self.excel_path = excel_path
        self.lock = threading.Lock()
        self._init_excel()

    def _init_excel(self):
        if self.excel_path.exists():
            try:
                self.df = pd.read_excel(self.excel_path)
                required_cols = ["PDF名称", "Markdown", "图片", "图片数量", "处理时间",
                                 "Dify状态", "Dify文件ID", "Dify结果", "Dify处理时间", "备注"]
                for col in required_cols:
                    if col not in self.df.columns:
                        self.df[col] = ""
                print(f"📖 读取现有Excel文件: {len(self.df)} 条记录")
            except Exception as e:
                print(f"⚠️ 读取Excel文件失败，创建新文件: {e}")
                self._create_new_excel()
        else:
            self._create_new_excel()

    def _create_new_excel(self):
        self.df = pd.DataFrame(columns=[
            "PDF名称", "Markdown", "图片", "图片数量", "处理时间",
            "Dify状态", "Dify文件ID", "Dify结果", "Dify处理时间", "备注"
        ])
        self._save_excel()
        print("📄 创建新的Excel记录文件")

    def _save_excel(self):
        try:
            self.excel_path.parent.mkdir(parents=True, exist_ok=True)
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                self.df.to_excel(writer, index=False, sheet_name='处理记录')
                ws = writer.sheets['处理记录']
                column_widths = {
                    'A': 25, 'B': 12, 'C': 10, 'D': 12, 'E': 18,
                    'F': 15, 'G': 25, 'H': 12, 'I': 18, 'J': 40
                }
                for col, width in column_widths.items():
                    ws.column_dimensions[col].width = width
        except Exception as e:
            print(f"❌ 保存Excel文件失败: {e}")

    def update_record(self, pdf_name: str, has_md: bool = None,
                      has_images: bool = None, image_count: int = 0,
                      dify_status: str = "", dify_file_id: str = "",
                      dify_result: str = "", note: str = ""):
        with self.lock:
            try:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                existing_idx = self.df[self.df['PDF名称'] == pdf_name].index

                if len(existing_idx) > 0:
                    idx = existing_idx[0]
                    if has_md is not None:
                        self.df.loc[idx, 'Markdown'] = "✅" if has_md else "❌"
                    if has_images is not None:
                        self.df.loc[idx, '图片'] = "✅" if has_images else "❌"
                    if image_count > 0:
                        self.df.loc[idx, '图片数量'] = image_count
                    if note:
                        self.df.loc[idx, '备注'] = note
                    if dify_status:
                        self.df.loc[idx, 'Dify状态'] = dify_status
                        self.df.loc[idx, 'Dify处理时间'] = current_time
                    if dify_file_id:
                        self.df.loc[idx, 'Dify文件ID'] = dify_file_id
                    if dify_result:
                        self.df.loc[idx, 'Dify结果'] = dify_result
                    if not self.df.loc[idx, '处理时间']:
                        self.df.loc[idx, '处理时间'] = current_time
                else:
                    new_record = {
                        "PDF名称": pdf_name,
                        "Markdown": "✅" if has_md else "❌" if has_md is not None else "",
                        "图片": "✅" if has_images else "❌" if has_images is not None else "",
                        "图片数量": image_count,
                        "处理时间": current_time,
                        "Dify状态": dify_status,
                        "Dify文件ID": dify_file_id,
                        "Dify结果": dify_result,
                        "Dify处理时间": current_time if dify_status else "",
                        "备注": note
                    }
                    self.df = pd.concat([self.df, pd.DataFrame([new_record])], ignore_index=True)

                self._save_excel()
            except Exception as e:
                print(f"❌ 更新记录失败: {e}")
