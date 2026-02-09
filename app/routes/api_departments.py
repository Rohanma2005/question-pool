# app/routes/api_departments.py
from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import Department

api_department_bp = Blueprint('api_department', __name__)

def is_super_admin():
    return session.get('role') == 'super_admin'

@api_department_bp.route('', methods=['GET'])
def get_departments():
    if not is_super_admin():
        return jsonify({"msg": "Forbidden"}), 403

    departments = Department.query.order_by(Department.id.desc()).all()
    return jsonify([{
        "id": d.id,
        "name": d.name
    } for d in departments]), 200

@api_department_bp.route('', methods=['POST'])
def create_department():
    if not is_super_admin():
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
        "department": {"id": dept.id, "name": dept.name}
    }), 201
