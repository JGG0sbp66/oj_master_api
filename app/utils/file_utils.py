import os
import zipfile
from werkzeug.utils import secure_filename
from datetime import datetime


def save_uploaded_file(file, upload_folder, prefix):
    """保存上传的文件，并添加前缀"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}_{secure_filename(file.filename)}"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return file_path


def extract_zip_file(zip_path, extract_dir):
    """
    解压ZIP文件并返回解压后的文件列表
    """
    # 删除目标目录中的所有内容
    if os.path.exists(extract_dir):
        for root, dirs, files in os.walk(extract_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(extract_dir)

    # 确保目标目录存在
    os.makedirs(extract_dir, exist_ok=True)

    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            # 防止目录遍历攻击
            if not file.startswith('..') and not file.startswith('/'):
                zip_ref.extract(file, extract_dir)
                extracted_files.append(file)

    return extracted_files