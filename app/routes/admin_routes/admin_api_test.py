from flask import Blueprint, make_response, jsonify

from app.utils.role_utils import role_required

admin_test_bp = Blueprint('admin_test', __name__)


@admin_test_bp.route('/admin-dashboard', methods=['GET'])
@role_required('admin')  # 只允许admin访问
def admin_dashboard():
    response = make_response(jsonify({
        'success': True,
        'message': 'IM ADMIN'
    }))
    return response
