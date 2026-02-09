# app/routes/api_programmes.py
from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import Programme, Department

api_programme_bp = Blueprint('api_programme', __name__)

def is_super_admin():
    return session.get('role') == 'super_admin'

@api_programme_bp.route('', methods=['GET'])
def get_programmes():
    if not is_super_admin():
        return jsonify({"msg": "Forbidden"}), 403

    programmes = Programme.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "department": p.department.name if p.department else None
    } for p in programmes]), 200

@api_programme_bp.route('', methods=['POST'])
def create_programme():
    if not is_super_admin():
        return jsonify({"msg": "Forbidden"}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    department_id = data.get('department_id')

    if not name or not department_id:
        return jsonify({"msg": "Name and department are required"}), 400

    dept = Department.query.get(department_id)
    if not dept:
        return jsonify({"msg": "Invalid department"}), 400

    programme = Programme(name=name, department_id=department_id)
    db.session.add(programme)
    db.session.commit()

    return jsonify({
        "id": programme.id,
        "name": programme.name,
        "department": dept.name
    }), 201
