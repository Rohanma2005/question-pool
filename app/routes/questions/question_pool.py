from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from app.extensions import db
from app.models import Course, Template, Topic, Question, ProgrammeCourseOffering, Faculty
from app.utils.auth import admin_or_hod_required, login_required


questions_bp = Blueprint(
    'questions',
    __name__,
    url_prefix='/superadmin/questions'
)


@questions_bp.route('', methods=['GET', 'POST'])
@login_required
def manage_questions():

    role = session.get('role')
    user_id = session.get('user_id')

    # ========================================
    # Determine Course Scope
    # ========================================
    if role == 'super_admin':
        courses = Course.query.all()

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
        return redirect(url_for('main.login'))

    selected_course_id = request.args.get('course_id', type=int)
    selected_topic_id = request.args.get('topic_id', type=int)

    template = None
    topics = []
    existing_questions = []

    if selected_course_id:
        template = Template.query.filter_by(
            course_id=selected_course_id
        ).first()

        topics = Topic.query.filter_by(
            course_id=selected_course_id
        ).all()

        if selected_topic_id:
            existing_questions = Question.query.filter_by(
                topic_id=selected_topic_id
            ).all()

    # ========================================
    # Handle Question Creation
    # ========================================
    if request.method == 'POST':

        if not template:
            flash("Template must exist before adding questions", "error")
            return redirect(request.url)

        topic_id = request.form.get('topic_id', type=int)
        text = request.form.get('text')
        question_type = request.form.get('question_type')
        mark_value = request.form.get('mark_value', type=int)
        difficulty = request.form.get('difficulty', type=int)
        topic = Topic.query.get(topic_id)
        if not topic or not topic.co:
            flash("Selected topic does not have an associated Course Outcome with Bloom Level", "error")
            return redirect(request.url)

        bloom_level = topic.co.bloom_level

        # Validate mark_value against template
        allowed_marks = {
            s["mark_per_question"]
            for s in template.categories
        }

        if mark_value not in allowed_marks:
            flash("Mark value not allowed by template", "error")
            return redirect(request.url)

        allowed_types = {
            s["question_type"]
            for s in template.categories
        }

        if question_type not in allowed_types:
            flash("Question type not allowed by template", "error")
            return redirect(request.url)

        options = None

        if question_type == "mcq":
            options = [
                request.form.get('option_1'),
                request.form.get('option_2'),
                request.form.get('option_3'),
                request.form.get('option_4')
            ]

            if not all(options):
                flash("All 4 options required for MCQ", "error")
                return redirect(request.url)

        question = Question(
            course_id=selected_course_id,
            topic_id=topic_id,
            text=text,
            question_type=question_type,
            mark_value=mark_value,
            difficulty=difficulty,
            bloom_level=bloom_level,
            options=options
        )

        db.session.add(question)
        db.session.commit()

        flash("Question added successfully", "success")
        return redirect(request.url)

    # Pass topics with their CO bloom level for the frontend JS
    topics_with_bloom = []
    for t in topics:
        topics_with_bloom.append({
            'id': t.id,
            'code': t.code,
            'title': t.title,
            'bloom_level': t.co.bloom_level if t.co else 'N/A'
        })

    return render_template(
        "question_management.html",
        courses=courses,
        topics=topics_with_bloom,
        template=template,
        existing_questions=existing_questions,
        selected_course_id=selected_course_id,
        selected_topic_id=selected_topic_id
    )


@questions_bp.route('/<int:question_id>/toggle', methods=['POST'])
@login_required
def toggle_question(question_id):

    question = Question.query.get_or_404(question_id)

    role = session.get('role')
    user_id = session.get('user_id')

    # Scope enforcement
    if role == 'faculty':
        faculty = Faculty.query.get(user_id)

        # Normal faculty → only assigned courses
        if faculty.department.hod_id != faculty.id:
            assigned_ids = {
                o.course_id
                for o in ProgrammeCourseOffering.query.filter_by(
                    faculty_id=faculty.id
                )
            }
            if question.course_id not in assigned_ids:
                flash("Not authorized", "error")
                return redirect(request.referrer)

        # HOD → only department owned courses
        else:
            if question.course.home_department_id != faculty.department.id:
                flash("Not authorized", "error")
                return redirect(request.referrer)

    question.active = not question.active
    db.session.commit()

    flash("Question status updated", "success")
    return redirect(request.referrer)
