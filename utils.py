# utils.py
import logging
import platform
import subprocess

def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pdf_processor_debug.log', encoding='utf-8')
        ]
    )

def open_dir(path):
    p = str(path)
    if platform.system() == "Windows":
        subprocess.Popen(['explorer', p])
    elif platform.system() == "Darwin":
        subprocess.Popen(['open', p])
    else:
        subprocess.Popen(['xdg-open', p])

def open_file(path):
    p = str(path)
    if platform.system() == "Windows":
        subprocess.Popen(['notepad', p])
    elif platform.system() == "Darwin":
        subprocess.Popen(['open', p])
    else:
        subprocess.Popen(['xdg-open', p])
