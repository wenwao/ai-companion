# storage.py
import json
import os
import base64

DATA_FILE = "sessions.json"

def load_sessions():
    """从磁盘加载所有会话，文件不存在则返回空字典"""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_sessions(sessions):
    """把会话字典写回磁盘，ensure_ascii=False 保留中文"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def image_to_base64(uploaded_file):
    """把 Streamlit 上传的图片转为 base64 字符串"""
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")