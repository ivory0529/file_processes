# ocr_processor.py
import json
import base64
from pathlib import Path
from datetime import datetime
from mistralai import Mistral, DocumentURLChunk, FileTypedDict
from config import Config

class PDFProcessor:
    def __init__(self, client: Mistral, tracker, dify_processor=None):
        import logging
        self.client = client
        self.tracker = tracker
        self.dify_processor = dify_processor
        self.logger = logging.getLogger(__name__)

    def process_pdf(self, pdf_path: Path, enable_dify: bool = False):
        pdf_name = pdf_path.name
        stem = pdf_path.stem
        self.logger.info(f"开始处理: {pdf_name}")
        self.tracker.update_record(pdf_name, note='正在OCR处理...')
        try:
            ocr_result = self._upload_and_ocr(pdf_path)
            img_count = self._save_images(ocr_result, stem)
            md_path = self._save_markdown(ocr_result, stem)

            has_md = md_path and md_path.exists()
            has_images = img_count > 0

            if has_md and has_images:
                note = "OCR完成"
            else:
                missing = []
                if not has_md: missing.append("MD")
                if not has_images: missing.append("图片")
                note = f"OCR部分缺失: {', '.join(missing)}"

            self.tracker.update_record(
                pdf_name,
                has_md=has_md,
                has_images=has_images,
                image_count=img_count,
                note=note
            )

            if enable_dify and has_md and self.dify_processor:
                self.logger.info(f"开始Dify处理: {pdf_name}")
                self.tracker.update_record(pdf_name, note="开始Dify处理...")

                dify_result = self.dify_processor.process_markdown(md_path, f"user_{stem}")

                if dify_result.get("success"):
                    if dify_result.get("found_result_file"):
                        note += " + Dify完成✅"
                    else:
                        note += " + Dify工作流成功但未生成文件⚠️"
                else:
                    dify_error = dify_result.get("error", "未知错误")
                    note += f" + Dify失败❌: {dify_error}"
                    self.logger.error(f"Dify处理失败: {dify_error}")

                self.tracker.update_record(pdf_name, note=note)

            self.logger.info(f"✅ 完成处理: {pdf_name} (图片: {img_count})")
            return has_md

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ 处理失败 {pdf_name}: {error_msg}")
            self.tracker.update_record(pdf_name, note=f"OCR错误: {error_msg}")
            return False

    def _upload_and_ocr(self, pdf_path: Path) -> dict:
        self.logger.info(f"上传PDF到Mistral: {pdf_path.name}")

        pdf_data = pdf_path.read_bytes()
        file_payload: FileTypedDict = FileTypedDict(
            file_name=pdf_path.stem,
            content=pdf_data
        )

        uploaded_file = self.client.files.upload(file=file_payload, purpose="ocr")

        try:
            signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id, expiry=1).url

            self.logger.info(f"执行OCR处理: {pdf_path.name}")
            ocr_response = self.client.ocr.process(
                document=DocumentURLChunk(document_url=signed_url),
                model=Config.MODEL_NAME,
                include_image_base64=True
            )

            return json.loads(ocr_response.model_dump_json())

        finally:
            try:
                self.client.files.delete(file_id=uploaded_file.id)
                self.logger.debug(f"清理上传文件: {uploaded_file.id}")
            except Exception as e:
                self.logger.warning(f"清理上传文件失败 {uploaded_file.id}: {e}")

    def _save_images(self, ocr_result: dict, stem: str) -> int:
        try:
            image_folder = Config.IMAGE_DIR / stem
            image_folder.mkdir(parents=True, exist_ok=True)
            image_count = 0
            self.logger.info(f"保存图片: {stem}")
            for page_idx, page in enumerate(ocr_result.get('pages', []), start=1):
                for img_idx, img in enumerate(page.get('images', []), start=1):
                    try:
                        base64_data = img.get('image_base64', '')
                        if not base64_data:
                            continue
                        if base64_data.startswith('data:'):
                            if ',' in base64_data:
                                _, actual_base64 = base64_data.split(',', 1)
                            else:
                                continue
                        else:
                            actual_base64 = base64_data
                        image_data = base64.b64decode(actual_base64)
                        format_ext = self._detect_image_format(image_data)
                        img_filename = f"{stem}_p{page_idx}_img{img_idx:02d}.{format_ext}"
                        img_path = image_folder / img_filename
                        img_path.write_bytes(image_data)
                        self.logger.debug(f"保存图片: {img_filename}")
                        image_count += 1
                    except Exception as e:
                        self.logger.error(f"处理图片失败: {e}")

            self.logger.info(f"完成图片保存: {image_count} 张")
            return image_count
        except Exception as e:
            self.logger.error(f"保存图片过程失败: {e}")
            return 0

    def _detect_image_format(self, image_data: bytes) -> str:
        if image_data.startswith(b'\xff\xd8\xff'):
            return 'jpg'
        elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            return 'gif'
        elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
            return 'webp'
        else:
            return 'jpg'

    def _save_markdown(self, ocr_result: dict, stem: str):
        try:
            self.logger.info(f"生成Markdown: {stem}")
            img_map = {}
            for page_idx, page in enumerate(ocr_result.get('pages', []), start=1):
                for img_idx, img in enumerate(page.get('images', []), start=1):
                    img_id = img.get('id', f"img_{img_idx}")
                    actual_format = 'jpg'
                    if img.get('image_base64'):
                        try:
                            base64_data = img.get('image_base64', '').split(',')[-1]
                            image_data = base64.b64decode(base64_data)
                            actual_format = self._detect_image_format(image_data)
                        except:
                            pass
                    actual_filename = f"{stem}_p{page_idx}_img{img_idx:02d}.{actual_format}"
                    actual_img_path = Config.IMAGE_DIR / stem / actual_filename
                    actual_rel_path = str(actual_img_path.relative_to(Config.MD_OUT_DIR.parent)).replace('\\', '/')
                    img_map[img_id] = actual_rel_path

            md_pages = []
            for page in ocr_result.get('pages', []):
                md_content = page.get('markdown', '')
                for img_id, img_path in img_map.items():
                    md_content = md_content.replace(
                        f"![{img_id}]({img_id})",
                        f"![{img_id}]({img_path})"
                    )
                md_pages.append(md_content)

            full_markdown = "\n\n".join(md_pages)
            header = f"""<!-- PDF处理信息 -->
<!-- 原始文件: {stem}.pdf -->
<!-- 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- 图片数量: {len(img_map)} -->

"""
            full_markdown = header + full_markdown
            Config.MD_OUT_DIR.mkdir(parents=True, exist_ok=True)
            md_path = Config.MD_OUT_DIR / f"{stem}.md"
            md_path.write_text(full_markdown, encoding='utf-8')
            self.logger.info(f"✅ Markdown保存完成: {md_path}")
            return md_path
        except Exception as e:
            self.logger.error(f"保存Markdown失败 {stem}: {e}")
            return None
