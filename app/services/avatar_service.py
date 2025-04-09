from flask import send_from_directory, jsonify

from app.utils.validators import is_safe_filename
from config import Config
import os


def get_avatar_service(user_id):
    """支持多格式的头像获取服务"""
    # 检查默认头像是否存在
    if not os.path.exists(os.path.join(Config.AVATAR_UPLOAD_DIR, Config.DEFAULT_AVATAR)):
        return jsonify({"success": False, "message": "默认头像不存在"}), 404

    # 用户未登录/未指定用户ID时返回默认头像
    if user_id is None:
        return send_avatar_file(Config.DEFAULT_AVATAR)

    # 尝试查找用户头像（支持多种格式）
    avatar_filename = find_user_avatar(user_id)
    return send_avatar_file(avatar_filename or Config.DEFAULT_AVATAR)


def send_avatar_file(filename):
    """安全发送头像文件"""
    if not is_safe_filename(filename):
        return jsonify({"success": False, "message": "非法文件名"}), 400

    try:
        return send_from_directory(
            directory=Config.AVATAR_UPLOAD_DIR,
            path=filename,
            max_age=3600
        )
    except FileNotFoundError:
        return jsonify({"success": False, "message": "头像文件不存在"}), 404


def find_user_avatar(user_id):
    """查找用户可能存在的头像文件（支持多格式）"""
    for ext in Config.ALLOWED_AVATAR_EXTENSIONS:
        filename = f"{user_id}.{ext}"
        filepath = os.path.join(Config.AVATAR_UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            return filename
    return None


def save_avatar(user_id, file):
    """保存用户上传的头像（自动处理格式）"""
    # 获取安全的文件扩展名
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in Config.ALLOWED_AVATAR_EXTENSIONS:
        raise ValueError("不支持的文件类型")

    # 删除用户旧头像（所有格式）
    delete_old_avatars(user_id)

    # 保存新头像（格式统一为user_id.ext）
    filename = f"{user_id}.{file_ext}"
    file.save(os.path.join(Config.AVATAR_UPLOAD_DIR, filename))
    return filename


def delete_old_avatars(user_id):
    """删除用户所有格式的旧头像"""
    for ext in Config.ALLOWED_AVATAR_EXTENSIONS:
        old_file = os.path.join(Config.AVATAR_UPLOAD_DIR, f"{user_id}.{ext}")
        try:
            os.remove(old_file)
        except FileNotFoundError:
            pass
