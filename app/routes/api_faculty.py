# app/routes/api_faculty.py
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import Faculty, Department

api_faculty_bp = Blueprint('api_faculty', __name__)

def is_super_admin():
    return session.get('role') == 'super_admin'

@api_faculty_bp.route('', methods=['GET'])
def get_faculties():
    if not is_super_admin():
        return jsonify({"msg": "Forbidden"}), 403

    faculties = Faculty.query.order_by(Faculty.id.desc()).all()
    return jsonify([{
        "id": f.id,
        "email": f.email,
        "department": f.department.name if f.department else None,
        "role": f.role
    } for f in faculties]), 200

@api_faculty_bp.route('', methods=['POST'])
def create_faculty():
    if not is_super_admin():
        return jsonify({"msg": "Forbidden"}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    department_id = data.get('department_id')

    if not name or not email or not password or not department_id:
        return jsonify({"msg": "Name, email, password and department are required"}), 400

    if Faculty.query.filter_by(email=email).first():
        return jsonify({"msg": "Faculty already exists"}), 409

    dept = Department.query.get(department_id)
    if not dept:
        return jsonify({"msg": "Invalid department"}), 400

    faculty = Faculty(
    name=name,
    email=email,
    password_hash=generate_password_hash(password),
    role='faculty',
    department_id=department_id
)

    db.session.add(faculty)
    db.session.commit()

    return jsonify({
        "msg": "Faculty created",
        "faculty": {
            "id": faculty.id,
            "email": faculty.email,
            "department": dept.name
        }
    }), 201
