import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import logging

from config import Config
from tracker import ProcessingTracker
from ocr_processor import PDFProcessor
from dify_processor import DifyProcessor
from utils import open_dir, open_file

class PDFProcessorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF文件批量处理器 - 增强调试版本")
        self.root.geometry("950x750")

        self.selected_files = []
        self.tracker = None
        self.processor = None
        self.processing = False

        self.setup_gui()
        self.setup_logging()

    def setup_logging(self):
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("🚀 PDF处理器启动 - 调试版本")
        logger.info("=" * 60)
        logger.info(f"📁 配置路径:")
        logger.info(f"   Markdown输出: {Config.MD_OUT_DIR}")
        logger.info(f"   图片输出: {Config.IMAGE_DIR}")
        logger.info(f"   Dify结果: {Config.DIFY_RESULT_DIR}")
        logger.info(f"   Excel记录: {Config.EXCEL_PATH}")
        logger.info(f"🔧 API状态:")
        logger.info(f"   Mistral: {'✅' if Config.MISTRAL_API_KEY else '❌'}")
        logger.info(f"   Dify: {'✅' if Config.DIFY_API_KEY else '❌'}")
        logger.info(f"   Dify服务器: {Config.DIFY_BASE_URL}")

    def setup_gui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="PDF文件批量处理器 - 调试增强版", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 配置状态和调试信息
        status_frame = ttk.LabelFrame(main_frame, text="系统状态 & 调试信息", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)

        # API状态
        mistral_status = "✅ 已配置" if Config.MISTRAL_API_KEY else "❌ 未配置 - OCR功能不可用"
        dify_status = "✅ 已配置" if Config.DIFY_API_KEY else "❌ 未配置 - Dify功能不可用"

        ttk.Label(status_grid, text="Mistral OCR API:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_grid, text=mistral_status).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(status_grid, text="Dify工作流API:").grid(row=1, column=0, sticky=tk.W, pady=(3, 0))
        ttk.Label(status_grid, text=dify_status).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(3, 0))

        ttk.Label(status_grid, text=f"Dify服务器:").grid(row=2, column=0, sticky=tk.W, pady=(3, 0))
        ttk.Label(status_grid, text=f"{Config.DIFY_BASE_URL}").grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(3, 0))

        ttk.Label(status_grid, text=f"Dify结果目录:").grid(row=3, column=0, sticky=tk.W, pady=(3, 0))
        ttk.Label(status_grid, text=f"{Config.DIFY_RESULT_DIR}").grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=(3, 0))

        # 调试按钮
        debug_frame = ttk.Frame(status_frame)
        debug_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(debug_frame, text="📁 打开Dify结果目录", command=self.open_dify_result_dir).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(debug_frame, text="📋 查看日志文件", command=self.open_log_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(debug_frame, text="🔄 检查Docker映射", command=self.check_docker_mapping).pack(side=tk.LEFT)

        # 处理选项
        options_frame = ttk.LabelFrame(main_frame, text="处理选项", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        self.enable_dify_var = tk.BooleanVar(value=Config.ENABLE_DIFY and bool(Config.DIFY_API_KEY))
        dify_check = ttk.Checkbutton(
            options_frame,
            text="启用Dify工作流处理（OCR完成后自动上传到Dify进行进一步处理）",
            variable=self.enable_dify_var,
            state='normal' if Config.DIFY_API_KEY else 'disabled'
        )
        dify_check.pack(anchor=tk.W)

        if not Config.DIFY_API_KEY:
            ttk.Label(options_frame, text="⚠️ 需要配置DIFY_API_KEY才能启用Dify功能", foreground="orange").pack(anchor=tk.W, pady=(5, 0))

        # 文件选择和处理区域
        process_frame = ttk.Frame(main_frame)
        process_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        process_frame.columnconfigure(1, weight=1)
        process_frame.rowconfigure(0, weight=1)

        # 按钮区域
        button_frame = ttk.Frame(process_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 15))

        ttk.Button(button_frame, text="选择PDF文件", command=self.select_files).grid(row=0, column=0, pady=(0, 8), sticky=tk.W)
        ttk.Button(button_frame, text="清空列表", command=self.clear_files).grid(row=1, column=0, pady=(0, 8), sticky=tk.W)
        ttk.Separator(button_frame, orient='horizontal').grid(row=2, column=0, pady=8, sticky=(tk.W, tk.E))

        self.start_button = ttk.Button(button_frame, text="🚀 开始处理", command=self.start_processing)
        self.start_button.grid(row=3, column=0, pady=(0, 8), sticky=tk.W)

        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止处理", command=self.stop_processing, state='disabled')
        self.stop_button.grid(row=4, column=0, pady=(0, 8), sticky=tk.W)

        # 文件列表
        list_frame = ttk.LabelFrame(process_frame, text="选择的文件", padding="10")
        list_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(list_frame, columns=('name', 'size', 'status'), show='headings')
        self.tree.heading('#1', text='文件名')
        self.tree.heading('#2', text='大小')
        self.tree.heading('#3', text='状态')
        self.tree.column('#1', width=350)
        self.tree.column('#2', width=100)
        self.tree.column('#3', width=200)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 进度信息
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.StringVar()
        self.progress_var.set("🎯 就绪 - 请选择PDF文件开始处理")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.grid(row=0, column=0, sticky=tk.W)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # API配置警告
        if not Config.MISTRAL_API_KEY or not Config.DIFY_API_KEY:
            warning_frame = ttk.Frame(main_frame)
            warning_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
            warnings = []
            if not Config.MISTRAL_API_KEY:
                warnings.append("MISTRAL_API_KEY未配置 - OCR功能不可用")
            if not Config.DIFY_API_KEY:
                warnings.append("DIFY_API_KEY未配置 - Dify功能不可用")
            warning_text = "⚠️ 配置警告: " + " | ".join(warnings)
            warning_label = ttk.Label(
                warning_frame,
                text=warning_text,
                foreground="red",
                font=("Arial", 9)
            )
            warning_label.pack()

    def open_dify_result_dir(self):
        try:
            Config.DIFY_RESULT_DIR.mkdir(parents=True, exist_ok=True)
            open_dir(Config.DIFY_RESULT_DIR)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {e}")

    def open_log_file(self):
        try:
            log_file = Path("pdf_processor_debug.log")
            if log_file.exists():
                open_file(log_file)
            else:
                messagebox.showinfo("信息", "日志文件尚未生成")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开日志文件: {e}")

    def check_docker_mapping(self):
        try:
            Config.DIFY_RESULT_DIR.mkdir(parents=True, exist_ok=True)
            test_file = Config.DIFY_RESULT_DIR / "mapping_test.txt"
            test_content = f"Docker映射测试\n创建时间: {Path(test_file).stat().st_mtime if test_file.exists() else '新建'}"
            test_file.write_text(test_content, encoding='utf-8')
            txt_files = list(Config.DIFY_RESULT_DIR.glob("*.txt"))
            file_list = "\n".join([f"📄 {f.name} ({Path(f).stat().st_mtime})" for f in txt_files])
            message = f"""Docker映射检查结果:

📁 目录: {Config.DIFY_RESULT_DIR}
📊 存在: {'是' if Config.DIFY_RESULT_DIR.exists() else '否'}
🔢 txt文件数量: {len(txt_files)}

文件列表:
{file_list if file_list else '(无txt文件)'}

✅ 测试文件已创建: mapping_test.txt"""
            messagebox.showinfo("Docker映射检查", message)
        except Exception as e:
            messagebox.showerror("错误", f"检查映射失败: {e}")

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')]
        )
        for file_path in files:
            path = Path(file_path)
            if path not in self.selected_files:
                self.selected_files.append(path)
        self.update_file_list()

    def clear_files(self):
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，无法清空列表")
            return
        self.selected_files.clear()
        self.update_file_list()

    def update_file_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for file_path in self.selected_files:
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            except Exception:
                size_str = "未知"
            self.tree.insert('', 'end', values=(file_path.name, size_str, "⏳ 待处理"))
        count = len(self.selected_files)
        if count == 0:
            self.progress_var.set("🎯 请选择PDF文件")
        else:
            self.progress_var.set(f"📋 已选择 {count} 个文件，准备处理")

    def update_file_status(self, file_path: Path, status: str):
        try:
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                if values[0] == file_path.name:
                    self.tree.item(item, values=(values[0], values[1], status))
                    break
            self.root.update_idletasks()
        except Exception:
            pass

    def start_processing(self):
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择PDF文件！")
            return
        if not Config.MISTRAL_API_KEY:
            messagebox.showerror("错误", "未配置Mistral API密钥！\n请在.env文件中设置MISTRAL_API_KEY")
            return
        if self.processing:
            messagebox.showinfo("提示", "正在处理中，请稍候...")
            return
        enable_dify = self.enable_dify_var.get()
        dify_text = "，并上传到Dify工作流进行进一步处理" if enable_dify else ""
        message = f"""🚀 确定要处理 {len(self.selected_files)} 个PDF文件吗？

📋 处理流程：
1. 📄 OCR提取文字和图片{dify_text}
2. 📝 生成Markdown文件
3. 🖼️ 保存提取的图片
4. 📊 记录处理结果到Excel

⏱️ 预计耗时：每个文件约1-3分钟
🔍 详细日志将保存到 pdf_processor_debug.log"""
        if not messagebox.askyesno("🔥 确认处理", message):
            return
        self.processing = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar['maximum'] = len(self.selected_files)
        self.progress_bar['value'] = 0
        try:
            self.tracker = ProcessingTracker(Config.EXCEL_PATH)
            from mistralai import Mistral
            client = Mistral(api_key=Config.MISTRAL_API_KEY)
            dify_processor = None
            if enable_dify and Config.DIFY_API_KEY:
                dify_processor = DifyProcessor(self.tracker)
            self.processor = PDFProcessor(client, self.tracker, dify_processor)
            threading.Thread(target=self._process_files, args=(enable_dify,), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"初始化处理器失败：{e}")
            self.processing = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')

    def stop_processing(self):
        if messagebox.askyesno("确认", "确定要停止处理吗？"):
            self.processing = False
            self.progress_var.set("🛑 用户停止处理")

    def _process_files(self, enable_dify: bool):
        logger = logging.getLogger(__name__)
        try:
            total_files = len(self.selected_files)
            success_count = 0
            logger.info(f"🚀 开始批量处理 {total_files} 个PDF文件")
            logger.info(f"🔧 Dify处理: {'启用' if enable_dify else '禁用'}")
            for i, file_path in enumerate(self.selected_files):
                if not self.processing:
                    logger.info(f"⏹️ 用户停止处理，已处理 {i} 个文件")
                    break
                logger.info(f"📄 开始处理第 {i + 1}/{total_files} 个文件: {file_path.name}")
                self.root.after(0, self.update_file_status, file_path, "🔄 OCR处理中...")
                self.root.after(0, self.progress_var.set, f"🔄 正在处理: {file_path.name} ({i + 1}/{total_files})")
                try:
                    success = self.processor.process_pdf(file_path, enable_dify)
                    if success:
                        success_count += 1
                        status = "✅ 处理完成"
                        logger.info(f"✅ 文件处理成功: {file_path.name}")
                    else:
                        status = "❌ 处理失败"
                        logger.error(f"❌ 文件处理失败: {file_path.name}")
                    self.root.after(0, self.update_file_status, file_path, status)
                except Exception as e:
                    logger.error(f"💥 处理文件异常 {file_path.name}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    self.root.after(0, self.update_file_status, file_path, f"❌ 错误: {str(e)[:30]}")
                self.root.after(0, self.progress_bar.config, {'value': i + 1})
            logger.info(f"🏁 批量处理完成: 成功 {success_count}/{total_files}")
            self.root.after(0, self._processing_completed, success_count, total_files)
        except Exception as e:
            logger.error(f"💥 处理过程严重异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.root.after(0, messagebox.showerror, "严重错误", f"处理过程中出错: {e}")
            self.root.after(0, self._processing_completed, 0, len(self.selected_files))

    def _processing_completed(self, success_count: int, total_files: int):
        self.processing = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        failed_count = total_files - success_count
        self.progress_var.set(f"🎉 处理完成！成功: {success_count}, 失败: {failed_count}")
        message = f"""🎉 处理完成！

📊 处理结果：
✅ 成功：{success_count} 个文件
❌ 失败：{failed_count} 个文件
📁 总计：{total_files} 个文件

📂 生成的文件：
📝 Markdown：{Config.MD_OUT_DIR}
🖼️ 图片：{Config.IMAGE_DIR}
📊 Excel记录：{Config.EXCEL_PATH}
🔧 Dify结果：{Config.DIFY_RESULT_DIR}
📋 详细日志：pdf_processor_debug.log

是否查看处理结果？"""
        if messagebox.askyesno("🎊 处理完成", message):
            self.open_results()

    def open_results(self):
        try:
            open_dir(Config.MD_OUT_DIR.parent)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {e}")

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("程序被用户中断")
