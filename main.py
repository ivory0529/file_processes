# main.py
from gui import PDFProcessorGUI
from utils import init_logging
from config import Config

def main():
    init_logging()
    print("=" * 80)
    print("🚀 PDF批量处理器 - 增强调试版本启动")
    print("=" * 80)
    print(f"📝 配置检查:")
    print(f"   Mistral API: {'✅ 已配置' if Config.MISTRAL_API_KEY else '❌ 未配置'}")
    print(f"   Dify API: {'✅ 已配置' if Config.DIFY_API_KEY else '❌ 未配置'}")
    print(f"   Dify服务器: {Config.DIFY_BASE_URL}")
    print(f"   输出目录:")
    print(f"     📝 Markdown: {Config.MD_OUT_DIR}")
    print(f"     🖼️ 图片: {Config.IMAGE_DIR}")
    print(f"     🔧 Dify结果: {Config.DIFY_RESULT_DIR}")
    print(f"     📊 Excel记录: {Config.EXCEL_PATH}")

    if not Config.MISTRAL_API_KEY:
        print("\n⚠️  警告：未配置Mistral API密钥！")
        print("   请在.env文件中添加：MISTRAL_API_KEY=your-api-key")
        print("   否则OCR功能将不可用")
    if not Config.DIFY_API_KEY:
        print("\n⚠️  提示：未配置Dify API密钥")
        print("   如需使用Dify工作流，请在.env文件中添加：DIFY_API_KEY=app-your-key")

    print(f"\n📋 详细日志将保存到: pdf_processor_debug.log")
    print(f"🎨 启动GUI界面...")

    try:
        app = PDFProcessorGUI()
        app.run()
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")

if __name__ == '__main__':
    main()
