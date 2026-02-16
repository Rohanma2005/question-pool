from flask import Blueprint, jsonify, request
from app.models import Course
from app.utils.auth import admin_or_hod_required

courses_api_bp = Blueprint(
    'courses_api',
    __name__,
    url_prefix='/api/courses'
)

@courses_api_bp.route('/by-department', methods=['GET'])
@admin_or_hod_required
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

@courses_api_bp.route('/', methods=['GET'])
@admin_or_hod_required
def get_courses():
    department_id = request.args.get('department_id', type=int)

    query = Course.query

    if department_id:
        query = query.filter_by(home_department_id=department_id)

    courses = query.order_by(Course.code).all()

    return jsonify([
        {
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "department": c.home_department.name
        }
        for c in courses
    ])
