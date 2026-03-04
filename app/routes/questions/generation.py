from flask import Blueprint, render_template, request, redirect, flash, session, url_for, jsonify
from app.extensions import db
from app.models import Course, Template, Topic, Question, GeneratedPaper, GeneratedPaperQuestion, Faculty, ProgrammeCourseOffering
from app.utils.auth import login_required
import random

generation_bp = Blueprint(
    'generation',
    __name__,
    url_prefix='/faculty/generation'
)

@generation_bp.route('', methods=['GET'])
@login_required
def generation_index():
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'super_admin':
        courses = Course.query.all()
    elif role == 'faculty':
        faculty = Faculty.query.get(user_id)
        if faculty.department.hod_id == faculty.id:
            courses = Course.query.filter_by(home_department_id=faculty.department.id).all()
        else:
            offerings = ProgrammeCourseOffering.query.filter_by(faculty_id=faculty.id).all()
            course_ids = {o.course_id for o in offerings}
            courses = Course.query.filter(Course.id.in_(course_ids)).all()
    else:
        return redirect(url_for('main.login'))

    selected_course_id = request.args.get('course_id', type=int)
    topics = []
    template_exists = False
    
    if selected_course_id:
        topics = Topic.query.filter_by(course_id=selected_course_id).all()
        template = Template.query.filter_by(course_id=selected_course_id).first()
        template_exists = template is not None

    # Prepare topics with their associated CO info for the frontend
    topics_data = []
    for t in topics:
        topics_data.append({
            'id': t.id,
            'code': t.code,
            'title': t.title,
            'co_code': t.co.code if t.co else "N/A",
            'co_description': t.co.description if t.co else "No CO description"
        })

    return render_template(
        'generate_paper.html',
        courses=courses,
        topics=topics_data,
        selected_course_id=selected_course_id,
        template_exists=template_exists
    )

@generation_bp.route('/generate', methods=['POST'])
@login_required
def generate_paper():
    course_id = request.form.get('course_id', type=int)
    topic_ids = request.form.getlist('topic_ids', type=int)

    if not all([course_id, topic_ids]):
        flash("Course and at least one Topic are required", "error")
        return redirect(url_for('generation.generation_index', course_id=course_id))

    template = Template.query.filter_by(
        course_id=course_id,
        is_active=True
    ).first()

    if not template:
        flash("No active template found for this course", "error")
        return redirect(url_for('generation.generate_paper_form'))

    # Start generation logic
    sections_questions = {}
    total_found_questions = 0
    
    for section in template.categories:
        # Filter questions matching criteria (multiple topics allowed)
        matching_questions = Question.query.filter(
            Question.course_id == course_id,
            Question.topic_id.in_(topic_ids),
            Question.question_type == section['question_type'],
            Question.mark_value == section['mark_per_question'],
            Question.active == True
        ).all()

        if len(matching_questions) < section['number_of_questions']:
            criteria = (
                f"Section: {section['section']}, "
                f"Type: {section['question_type']}, "
                f"Marks: {section['mark_per_question']}"
            )
            flash(
                f"Insufficient questions. Required: {section['number_of_questions']}, "
                f"Available: {len(matching_questions)} for criteria [{criteria}]", 
                "error"
            )
            return redirect(url_for('generation.generation_index', course_id=course_id))

        # Randomly select questions
        selected_questions = random.sample(matching_questions, section['number_of_questions'])
        sections_questions[section['section']] = selected_questions
        total_found_questions += len(selected_questions)

    # Save GeneratedPaper
    paper = GeneratedPaper(
        course_id=course_id,
        template_id=template.id,
        total_marks=template.total_marks,
        duration_minutes=template.duration_minutes,
        generated_by=session['user_id'],
        co_weightages_snapshot={} # Placeholder for now as requested simple generation
    )
    db.session.add(paper)
    db.session.flush() # Get paper.id

    order = 1
    for section_label, questions in sections_questions.items():
        for q in questions:
            gp_question = GeneratedPaperQuestion(
                paper_id=paper.id,
                question_id=q.id,
                order=order,
                mark_value=q.mark_value,
                section_label=section_label,
                co_satisfied=q.topic.co.code if q.topic and q.topic.co else "N/A"
            )
            db.session.add(gp_question)
            order += 1

    db.session.commit()

    flash("Question paper generated successfully", "success")
    return redirect(url_for('generation.view_paper', paper_id=paper.id))

@generation_bp.route('/history')
@login_required
def paper_history():
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'super_admin':
        papers = GeneratedPaper.query.order_by(GeneratedPaper.created_at.desc()).all()
    elif role == 'faculty':
        faculty = Faculty.query.get(user_id)
        if faculty.department.hod_id == faculty.id:
            # HOD can see papers for their department's courses
            courses = Course.query.filter_by(home_department_id=faculty.department.id).all()
            course_ids = [c.id for c in courses]
            papers = GeneratedPaper.query.filter(GeneratedPaper.course_id.in_(course_ids)).order_by(GeneratedPaper.created_at.desc()).all()
        else:
            # Faculty can see papers they generated
            papers = GeneratedPaper.query.filter_by(generated_by=user_id).order_by(GeneratedPaper.created_at.desc()).all()
    else:
        return redirect(url_for('main.login'))

    # Group papers by course
    grouped_papers = {}
    for p in papers:
        c_name = f"[{p.course.code}] {p.course.title}" if p.course else "Unknown Course"
        if c_name not in grouped_papers:
            grouped_papers[c_name] = []
        grouped_papers[c_name].append(p)

    return render_template(
        'generated_papers_list.html',
        grouped_papers=grouped_papers
    )

@generation_bp.route('/paper/<int:paper_id>')
@login_required
def view_paper(paper_id):
    paper = GeneratedPaper.query.get_or_404(paper_id)
    course = Course.query.get(paper.course_id)
    
    # Group questions by section label
    sections = {}
    for gp_q in paper.questions:
        label = gp_q.section_label
        if label not in sections:
            sections[label] = []
        
        # Load the actual question text and options
        actual_q = Question.query.get(gp_q.question_id)
        sections[label].append({
            'text': actual_q.text,
            'mark_value': gp_q.mark_value,
            'question_type': actual_q.question_type,
            'options': actual_q.options,
            'co_satisfied': gp_q.co_satisfied
        })

    # Prepare section metadata (required vs total)
    section_meta = {}
    if paper.template:
        for cat in paper.template.categories:
            section_meta[cat['section']] = {
                'required': cat.get('required_questions', cat['number_of_questions']),
                'total': cat['number_of_questions']
            }

    return render_template(
        'view_generated_paper.html',
        paper=paper,
        course=course,
        sections=sections,
        section_meta=section_meta,
        hide_sidebar=True
    )
