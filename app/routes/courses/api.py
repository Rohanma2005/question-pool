from flask import Blueprint, jsonify, request
from app.models import Course
from app.routes.main import super_admin_required

courses_api_bp = Blueprint(
    'courses_api',
    __name__,
    url_prefix='/api/courses'
)

@courses_api_bp.route('/by-department', methods=['GET'])
@super_admin_required
def courses_by_department():
    department_id = request.args.get('department_id', type=int)

    if not department_id:
        return jsonify([])

    courses = Course.query.filter_by(
        home_department_id=department_id
    ).order_by(Course.code).all()

    return jsonify([
        {
            "id": c.id,
            "code": c.code,
            "title": c.title
        }
        for c in courses
    ])
