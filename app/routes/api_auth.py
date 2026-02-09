# app/routes/api_auth.py
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
from ..extensions import db
from ..models import SuperAdmin, Faculty

api_auth_bp = Blueprint('api_auth', __name__)

@api_auth_bp.route('/superadmin/login', methods=['POST'])
def api_superadmin_login():
    data = request.get_json() or {}
    email = (data.get('email') or "").strip().lower()
    password = data.get('password') or ""

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    admin = SuperAdmin.query.filter(
        db.func.lower(db.func.trim(SuperAdmin.email)) == email
    ).first()

    if not admin or not admin.check_password(password):
        return jsonify({"msg": "Bad credentials"}), 401

    session['user_id'] = admin.id
    session['role'] = 'super_admin'
    session['email'] = admin.email
    
    return jsonify({"msg": "Login successful"}), 200

@api_auth_bp.route('/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"msg": "Logged out"}), 200

@api_auth_bp.route('/check', methods=['GET'])
def api_check_auth():
    if 'user_id' not in session:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "role": session.get('role')}), 200
