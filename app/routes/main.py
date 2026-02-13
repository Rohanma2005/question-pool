# app/routes/main.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import SuperAdmin, Faculty, Department, Programme, ProgrammeCourseOffering , Course
from functools import wraps
import secrets

main_bp = Blueprint('main', __name__)


# =====================================================
# DECORATORS
# =====================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first', 'error')
            return redirect(url_for('main.superadmin_login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'super_admin':
           if request.endpoint and request.endpoint.startswith('main.superadmin_login'):
            return redirect(url_for('main.superadmin_login'))

            flash('Access denied', 'error')
            return redirect(url_for('main.superadmin_login'))

        return f(*args, **kwargs)
    return decorated_function

def verify_csrf_token():
    """Verify CSRF token from form or headers"""
    token = session.get('csrf_token')
    if not token:
        return False
    
    form_token = request.form.get('csrf_token', '') or request.headers.get('X-CSRF-Token', '')
    return secrets.compare_digest(token, form_token)

# =====================================================
# AUTH ROUTES
# =====================================================
@main_bp.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        if session.get('role') == 'super_admin':
            return redirect(url_for('main.superadmin_dashboard'))
        else:
            return redirect(url_for('main.faculty_dashboard'))
    return redirect(url_for('main.superadmin_login'))

@main_bp.route('/superadmin/login', methods=['GET', 'POST'])
def superadmin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password required', 'error')
            return redirect(url_for('main.superadmin_login'))

        admin = SuperAdmin.query.filter(
            db.func.lower(db.func.trim(SuperAdmin.email)) == email
        ).first()

        if admin and admin.check_password(password):
            session['user_id'] = admin.id
            session['role'] = 'super_admin'
            session['email'] = admin.email
            session['csrf_token'] = secrets.token_hex(32)
            flash('Login successful!', 'success')
            return redirect(url_for('main.superadmin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    # Generate CSRF token for login form
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)

    return render_template('superadmin_login.html')

@main_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('main.superadmin_login'))

# =====================================================
# SUPER ADMIN DASHBOARD
# =====================================================
@main_bp.route('/superadmin/dashboard', methods=['GET', 'POST'])
@super_admin_required
def superadmin_dashboard():
    if request.method == 'POST':
        if not verify_csrf_token():
            flash('CSRF token invalid', 'error')
            return redirect(url_for('main.superadmin_dashboard'))
            
        dept_name = request.form.get('dept_name', '').strip()
        if not dept_name:
            flash('Department name is required', 'error')
        elif Department.query.filter_by(name=dept_name).first():
            flash('Department already exists', 'error')
        else:
            dept = Department(name=dept_name)
            db.session.add(dept)
            db.session.commit()
            flash('Department created successfully!', 'success')
        return redirect(url_for('main.superadmin_dashboard'))

    departments = Department.query.order_by(Department.id.desc()).all()
    return render_template('superadmin_dashboard.html', departments=departments)

# =====================================================
# FACULTY MANAGEMENT
# =====================================================
@main_bp.route('/superadmin/faculties', methods=['GET', 'POST'])
@super_admin_required
def faculty_management():
    if request.method == 'POST':
        if not verify_csrf_token():
            flash('CSRF token invalid', 'error')
            return redirect(url_for('main.faculty_management'))
            
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        department_id = request.form.get('department_id')

        if not name or not email or not password or not department_id:
            flash('All fields are required', 'error')

        elif Faculty.query.filter_by(email=email).first():
            flash('Faculty already exists', 'error')
        else:
            dept = Department.query.get(department_id)
            if not dept:
                flash('Invalid department', 'error')
            else:
                faculty = Faculty(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash(password),
                    role='faculty',
                    department_id=department_id
                )
                db.session.add(faculty)
                db.session.commit()
                flash('Faculty created successfully!', 'success')
        return redirect(url_for('main.faculty_management'))

    faculties = Faculty.query.order_by(Faculty.id.desc()).all()
    departments = Department.query.all()
    return render_template('faculty_management.html', 
                         faculties=faculties, 
                         departments=departments)

# =====================================================
# PROGRAMME MANAGEMENT
# =====================================================
@main_bp.route('/superadmin/programmes', methods=['GET', 'POST'])
@super_admin_required
def programme_management():
    if request.method == 'POST':
        if not verify_csrf_token():
            flash('CSRF token invalid', 'error')
            return redirect(url_for('main.programme_management'))
            
        name = request.form.get('name', '').strip()
        department_id = request.form.get('department_id')

        if not name or not department_id:
            flash('Programme name and department are required', 'error')
        else:
            dept = Department.query.get(department_id)
            if not dept:
                flash('Invalid department', 'error')
            else:
                programme = Programme(name=name, department_id=department_id)
                db.session.add(programme)
                db.session.commit()
                flash('Programme created successfully!', 'success')
        return redirect(url_for('main.programme_management'))

    programmes = Programme.query.all()
    departments = Department.query.all()
    return render_template('programmes.html', 
                         programmes=programmes, 
                         departments=departments)

@main_bp.route(
    '/superadmin/programmes/<int:programme_id>',
    methods=['GET', 'POST']
)

@super_admin_required
def programme_detail(programme_id):
    programme = Programme.query.get_or_404(programme_id)
    departments = Department.query.order_by(Department.name).all()

    semester_no = request.args.get('semester', 1, type=int)
    if semester_no < 1 or semester_no > 8:
     semester_no = 1


    # ==========================
    # HANDLE ADD COURSE (POST)
    # ==========================
    if request.method == 'POST':
        course_id = request.form.get('course_id', type=int)
        faculty_id = request.form.get('faculty_id', type=int)

        if not course_id or not faculty_id:
            flash('Course and faculty are required', 'error')
            return redirect(
                url_for(
                    'programme_detail.programme_detail',
                    programme_id=programme.id,
                    semester=semester_no
                )
            )

        # Prevent duplicate course in programme
        exists = ProgrammeCourseOffering.query.filter_by(
            programme_id=programme.id,
            course_id=course_id
        ).first()

        if exists:
            flash('This course is already added to the programme', 'error')
        else:
            offering = ProgrammeCourseOffering(
                programme_id=programme.id,
                course_id=course_id,
                semester_no=semester_no,
                faculty_id=faculty_id
            )
            db.session.add(offering)
            db.session.commit()
            flash('Course added to semester successfully', 'success')

        return redirect(
            url_for(
                'main.programme_detail',
                programme_id=programme.id,
                semester=semester_no
            )
        )

    # ==========================
    # GET DATA FOR VIEW
    # ==========================
    offerings = ProgrammeCourseOffering.query.filter_by(
        programme_id=programme.id,
        semester_no=semester_no
    ).all()

    courses = Course.query.order_by(Course.code).all()
    faculties = Faculty.query.order_by(Faculty.name).all()

    return render_template(
    'programme_detail.html',
    programme=programme,
    semester_no=semester_no,
    offerings=offerings,
    courses=courses,
    faculties=faculties,
    departments=departments
)



# =====================================================
# DELETE ROUTES
# =====================================================
@main_bp.route('/departments/<int:dept_id>/delete', methods=['POST'])
@super_admin_required
def delete_department(dept_id):
    if not verify_csrf_token():
        flash('CSRF token invalid', 'error')
        return redirect(url_for('main.superadmin_dashboard'))
        
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted successfully', 'success')
    return redirect(url_for('main.superadmin_dashboard'))

@main_bp.route('/faculties/<int:faculty_id>/delete', methods=['POST'])
@super_admin_required
def delete_faculty(faculty_id):
    if not verify_csrf_token():
        flash('CSRF token invalid', 'error')
        return redirect(url_for('main.faculty_management'))
        
    faculty = Faculty.query.get_or_404(faculty_id)
    db.session.delete(faculty)
    db.session.commit()
    flash('Faculty deleted successfully', 'success')
    return redirect(url_for('main.faculty_management'))

@main_bp.route('/programmes/<int:programme_id>/delete', methods=['POST'])
@super_admin_required
def delete_programme(programme_id):
    if not verify_csrf_token():
        flash('CSRF token invalid', 'error')
        return redirect(url_for('main.programme_management'))
        
    programme = Programme.query.get_or_404(programme_id)
    db.session.delete(programme)
    db.session.commit()
    flash('Programme deleted successfully', 'success')
    return redirect(url_for('main.programme_management'))

# =====================================================
# PLACEHOLDER FOR FACULTY ROUTES
# =====================================================
@main_bp.route('/faculty/dashboard', methods=['GET'])
@login_required
def faculty_dashboard():
    # Placeholder for faculty dashboard
    return render_template('faculty_dashboard.html')
