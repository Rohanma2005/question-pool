from flask import render_template, request, redirect, url_for, flash, Blueprint
from app.extensions import db
from app.models import Department, Faculty
from app.utils.auth import admin_or_hod_required


departments_bp = Blueprint(
    'departments',
    __name__,
    url_prefix='/superadmin/departments'
)


@departments_bp.route('/<int:dept_id>', methods=['GET', 'POST'])
@admin_or_hod_required
def department_detail(dept_id):
    department = Department.query.get_or_404(dept_id)

    if request.method == 'POST':
        new_hod_id = request.form.get('hod_id', type=int)

        if new_hod_id:
            faculty = Faculty.query.filter_by(
                id=new_hod_id,
                department_id=department.id
            ).first()

            if not faculty:
                flash('Invalid faculty selected', 'error')
            else:
                department.hod_id = faculty.id
                db.session.commit()
                flash('HOD updated successfully', 'success')

        return redirect(request.url)

    faculties = Faculty.query.filter_by(
        department_id=department.id
    ).all()

    return render_template(
        'department_detail.html',
        department=department,
        faculties=faculties
    )
