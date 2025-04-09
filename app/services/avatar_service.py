from flask import send_from_directory, jsonify

from app.utils.validators import is_safe_filename
from config import Config
import os


def get_avatar_service(user_id):
    # 验证文件路径安全
    filename = f"{user_id}.png"
    if not is_safe_filename(filename):
        return jsonify({"success": False, "message": "非法文件名"}), 400

    # 检查文件是否存在
    filepath = os.path.join(Config.AVATAR_UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        filename = Config.DEFAULT_AVATAR  # 默认头像文件名
    filepath = os.path.join(Config.AVATAR_UPLOAD_DIR, filename)

    print(filepath)

    # 发送文件（自动处理缓存和MIME类型）
    return send_from_directory(
        directory=Config.AVATAR_UPLOAD_DIR,
        path=filename,
        max_age=3600  # 客户端缓存1小时
    )
