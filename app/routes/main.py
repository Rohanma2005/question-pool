# app/routes/main.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import SuperAdmin, Faculty, Department, Programme, ProgrammeCourseOffering , Course
from functools import wraps
import secrets
from ..utils.auth import login_required, admin_or_hod_required, verify_csrf_token

main_bp = Blueprint('main', __name__)


# =====================================================
# DECORATORS
# =====================================================


# =====================================================
# AUTH ROUTES
# =====================================================
@main_bp.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        if session.get('role') == 'super_admin':
            return redirect(url_for('main.superadmin_dashboard'))
        else:
            return redirect(url_for('faculty.faculty_dashboard'))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password required', 'error')
            return redirect(url_for('main.login'))

        # Try SuperAdmin
        admin = SuperAdmin.query.filter(
            db.func.lower(SuperAdmin.email) == email
        ).first()

        if admin and admin.check_password(password):
            session['user_id'] = admin.id
            session['role'] = 'super_admin'
            return redirect(url_for('main.superadmin_dashboard'))

        # Try Faculty
        faculty = Faculty.query.filter(
            db.func.lower(Faculty.email) == email
        ).first()

        if faculty and check_password_hash(faculty.password_hash, password):
            session['user_id'] = faculty.id
            session['role'] = 'faculty'

            # HOD detection
            if faculty.department.hod_id == faculty.id:
                return redirect(url_for('main.superadmin_dashboard'))

            return redirect(url_for('faculty.faculty_dashboard'))

        flash('Invalid credentials', 'error')

    return render_template('login.html')


@main_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('main.login'))

# =====================================================
# SUPER ADMIN DASHBOARD
# =====================================================
@main_bp.route('/superadmin/dashboard')
@admin_or_hod_required
def superadmin_dashboard():

    role = session.get('role')
    is_superadmin = session.get('role') == 'super_admin'

    if role == 'super_admin':
        departments = Department.query.order_by(
            Department.id.desc()
        ).all()

        return render_template(
            'superadmin_dashboard.html',
            departments=departments,
            is_superadmin=True
        )

    elif role == 'faculty':
        faculty = Faculty.query.get(session['user_id'])

        # HOD goes directly to their department
        return redirect(
            url_for(
                'departments.department_detail',
                dept_id=faculty.department.id,
                is_superadmin=is_superadmin
            )
        )


# =====================================================
# FACULTY MANAGEMENT
# =====================================================
@main_bp.route('/superadmin/faculties', methods=['GET', 'POST'])
@admin_or_hod_required
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
@admin_or_hod_required
def programme_management():

    role = session.get('role')

    # =========================
    # Determine Scope
    # =========================
    if role == 'super_admin':
        departments = Department.query.all()
        programmes_query = Programme.query

    else:  # HOD
        faculty = Faculty.query.get(session['user_id'])
        department = faculty.department

        departments = [department]  # HOD can only see own dept
        programmes_query = Programme.query.filter_by(
            department_id=department.id
        )

    # =========================
    # Handle Create
    # =========================
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department_id = request.form.get('department_id', type=int)

        if not name or not department_id:
            flash('Programme name and department are required', 'error')
            return redirect(request.url)

        # HOD cannot create in other departments
        if role == 'faculty':
            if department_id != department.id:
                flash('Not authorized for this department', 'error')
                return redirect(request.url)

        dept = Department.query.get(department_id)
        if not dept:
            flash('Invalid department', 'error')
            return redirect(request.url)

        programme = Programme(
            name=name,
            department_id=department_id
        )

        db.session.add(programme)
        db.session.commit()

        flash('Programme created successfully', 'success')
        return redirect(request.url)

    programmes = programmes_query.all()

    return render_template(
        'programmes.html',
        programmes=programmes,
        departments=departments,
        is_superadmin=(role == 'super_admin')
    )


@main_bp.route(
    '/superadmin/programmes/<int:programme_id>',
    methods=['GET', 'POST']
)

@admin_or_hod_required
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
@admin_or_hod_required
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
@admin_or_hod_required
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
@admin_or_hod_required
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
