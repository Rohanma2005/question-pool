from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from app.extensions import db
from app.models import Template, Course, Faculty, ProgrammeCourseOffering
from app.utils.auth import admin_or_hod_required,login_required

templates_bp = Blueprint(
    'templates',
    __name__,
    url_prefix='/superadmin/templates'
)

@templates_bp.route('', methods=['GET', 'POST'])
@login_required
def manage_template():

    role = session.get('role')
    user_id = session.get('user_id')

    # =========================================
    # Determine Course Scope
    # =========================================
    if role == 'super_admin':
        courses = Course.query.order_by(Course.code).all()

    elif role == 'faculty':
        faculty = Faculty.query.get(user_id)

        if faculty.department.hod_id == faculty.id:
            courses = Course.query.filter_by(
                home_department_id=faculty.department.id
            ).all()
        else:
            offerings = ProgrammeCourseOffering.query.filter_by(
                faculty_id=faculty.id
            ).all()

            course_ids = {o.course_id for o in offerings}
            courses = Course.query.filter(
                Course.id.in_(course_ids)
            ).all()
    else:
        flash("Unauthorized", "error")
        return redirect(url_for('main.login'))

    selected_course_id = request.args.get('course_id', type=int)
    archived_id = request.args.get('archived_id', type=int)
    template = None
    edit_mode = False
    viewing_archived = False

    if selected_course_id:
        if archived_id:
            template = Template.query.filter_by(
                id=archived_id,
                course_id=selected_course_id
            ).first()
            if template and not template.is_active:
                viewing_archived = True
        else:
            template = Template.query.filter_by(
                course_id=selected_course_id,
                is_active=True
            ).first()

        if request.args.get("edit") == "true" and not viewing_archived:
            edit_mode = True

    # =========================================
    # Handle Create / Update / Restore
    # =========================================
    if request.method == 'POST':
        action = request.form.get('action', 'save')
        course_id = request.form.get('course_id', type=int)

        if action == 'restore':
            restore_id = request.form.get('restore_id', type=int)
            template_to_restore = Template.query.filter_by(id=restore_id, course_id=course_id).first()
            if template_to_restore and not template_to_restore.is_active:
                # Archive currently active
                active_template = Template.query.filter_by(course_id=course_id, is_active=True).first()
                if active_template:
                    active_template.is_active = False
                
                # Restore the selected one
                template_to_restore.is_active = True
                db.session.commit()
                flash("Archived template restored and is now active.", "success")
            else:
                flash("Invalid template or already active.", "error")
            return redirect(url_for('templates.manage_template', course_id=course_id))
        total_marks = request.form.get('total_marks', type=int)
        duration = request.form.get('duration_minutes', type=int)
        section_count = request.form.get('section_count', type=int)

        template = Template.query.filter_by(
            course_id=course_id,
            is_active=True
        ).first()

        sections = []
        for i in range(section_count):
            sections.append({
                "section": request.form.get(f'section_{i}_name'),
                "question_type": request.form.get(f'section_{i}_type'),
                "mark_per_question": request.form.get(
                    f'section_{i}_mark', type=int
                ),
                "number_of_questions": request.form.get(
                    f'section_{i}_count', type=int
                ),
                "required_questions": request.form.get(
                    f'section_{i}_required', type=int
                )
            })

        calculated_total = sum(
            s["mark_per_question"] * s["required_questions"]
            for s in sections
        )

        if calculated_total != total_marks:
            flash("Section marks do not match total marks", "error")
            return redirect(request.url)

        # Always create a new template instance
        new_template = Template(
            course_id=course_id,
            duration_minutes=duration,
            total_marks=total_marks,
            categories=sections,
            is_active=True
        )

        # Archive the old template if it exists
        if template:
            template.is_active = False

        db.session.add(new_template)

        db.session.commit()
        flash("Template saved successfully", "success")
        return redirect(
            url_for('templates.manage_template',
                    course_id=course_id)
        )

    archived_templates = []
    if selected_course_id:
        archived_templates = Template.query.filter_by(
            course_id=selected_course_id,
            is_active=False
        ).order_by(Template.created_at.desc()).all()

    return render_template(
        "template_management.html",
        courses=courses,
        selected_course_id=selected_course_id,
        template=template,
        edit_mode=edit_mode,
        viewing_archived=viewing_archived,
        archived_templates=archived_templates
    )

