from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import Department, Faculty

api_department_bp = Blueprint('api_department', __name__)


def get_current_user():
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'super_admin':
        return role, None

    if role == 'faculty':
        faculty = Faculty.query.get(user_id)
        return role, faculty

    return None, None


# ========================================
# GET DEPARTMENTS
# ========================================
@api_department_bp.route('', methods=['GET'])
def get_departments():
    role, faculty = get_current_user()
    is_superadmin = session.get('role') == 'super_admin'

    # SuperAdmin → all departments
    if role == 'super_admin':
        departments = Department.query.order_by(
            Department.id.desc()
        ).all()

    # HOD → only own department
    elif role == 'faculty' and faculty and faculty.department.hod_id == faculty.id:
        departments = [faculty.department]

    else:
        return jsonify({"msg": "Forbidden"}), 403

    return jsonify([
        {
            "id": d.id,
            "name": d.name
        }
        for d in departments
    ]), 200


# ========================================
# CREATE DEPARTMENT
# ========================================
@api_department_bp.route('', methods=['POST'])
def create_department():
    role = session.get('role')

    # Only SuperAdmin can create departments
    if role != 'super_admin':
        return jsonify({"msg": "Forbidden"}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()

    if not name:
        return jsonify({"msg": "Department name is required"}), 400

    if Department.query.filter_by(name=name).first():
        return jsonify({"msg": "Department already exists"}), 409

    dept = Department(name=name)
    db.session.add(dept)
    db.session.commit()

    return jsonify({
        "msg": "Department created",
        "department": {
            "id": dept.id,
            "name": dept.name
        }
    }), 201
