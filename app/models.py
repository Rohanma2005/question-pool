from datetime import datetime
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

# =====================================================
# SUPER ADMINS
# =====================================================
class SuperAdmin(db.Model):
    __tablename__ = 'tbl_superadmins'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


# =====================================================
# DEPARTMENT
# =====================================================
class Department(db.Model):
    __tablename__ = 'tbl_departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)

    # HOD reference
    hod_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_faculty.id'),
        nullable=True
    )

    hod = db.relationship(
        'Faculty',
        foreign_keys=[hod_id],
        post_update=True
    )

    programmes = db.relationship(
        'Programme',
        backref='department',
        cascade='all,delete',
        lazy=True
    )

    faculties = db.relationship(
        'Faculty',
        backref='department',
        cascade='all,delete',
        lazy=True,
        foreign_keys='Faculty.department_id'   # ✅ CRITICAL FIX
    )




# =====================================================
# FACULTY
# =====================================================
class Faculty(db.Model):
    __tablename__ = 'tbl_faculty'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(128), nullable=False)  # ✅ NEW

    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False)  # 'faculty'

    department_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_departments.id'),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# PROGRAMME
# =====================================================
class Programme(db.Model):
    __tablename__ = 'tbl_programmes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_departments.id'),
        nullable=False
    )

    # programme → semester → courses (via offerings)
    course_offerings = db.relationship(
        'ProgrammeCourseOffering',
        backref='programme',
        cascade='all,delete',
        lazy=True
    )


# =====================================================
# COURSE (GLOBAL)
# =====================================================
class Course(db.Model):
    __tablename__ = 'tbl_courses'

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(256), nullable=False)

    # Home / owning department
    home_department_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_departments.id'),
        nullable=False
    )

    home_department = db.relationship('Department')

    # programme-specific appearances
    programme_offerings = db.relationship(
        'ProgrammeCourseOffering',
        backref='course',
        cascade='all,delete',
        lazy=True
    )

    # Academic structure (global)
    course_outcomes = db.relationship(
        'CourseOutcome',
        backref='course',
        cascade='all,delete',
        lazy=True
    )

    topics = db.relationship(
        'Topic',
        backref='course',
        cascade='all,delete',
        lazy=True
    )

    # ONE template per course (GLOBAL)
    template = db.relationship(
        'Template',
        uselist=False,
        backref='course',
        cascade='all,delete'
    )

    questions = db.relationship(
        'Question',
        backref='course',
        cascade='all,delete',
        lazy=True
    )


# =====================================================
# PROGRAMME – COURSE – SEMESTER – FACULTY (CORE TABLE)
# =====================================================
class ProgrammeCourseOffering(db.Model):
    __tablename__ = 'tbl_programme_course_offerings'

    id = db.Column(db.Integer, primary_key=True)

    programme_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_programmes.id'),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_courses.id'),
        nullable=False
    )

    semester_no = db.Column(
        db.Integer,
        nullable=False
    )  # 1–6

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_faculty.id'),
        nullable=False
    )

    faculty = db.relationship('Faculty')

    __table_args__ = (
        db.UniqueConstraint(
            'programme_id',
            'course_id',
            name='uq_programme_course_once'
        ),
        db.CheckConstraint(
    'semester_no BETWEEN 1 AND 8',
    name='chk_semester_range'
)
,
    )


# =====================================================
# COURSE OUTCOMES
# =====================================================
class CourseOutcome(db.Model):
    __tablename__ = 'tbl_course_outcomes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), nullable=False)  # CO1, CO2
    description = db.Column(db.Text, nullable=False)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_courses.id'),
        nullable=False
    )

    topics = db.relationship(
        'Topic',
        backref='co',
        cascade='all,delete',
        lazy=True
    )


# =====================================================
# TOPICS
# =====================================================
class Topic(db.Model):
    __tablename__ = 'tbl_topics'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32))  # e.g., 1.1
    title = db.Column(db.Text, nullable=False)

    parent_topic_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_topics.id'),
        nullable=True
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_courses.id'),
        nullable=False
    )

    co_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_course_outcomes.id'),
        nullable=False
    )

    parent = db.relationship(
        'Topic',
        remote_side=[id],
        backref='children'
    )


# =====================================================
# TEMPLATE
# =====================================================
class Template(db.Model):
    __tablename__ = 'tbl_templates'

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_courses.id'),
        nullable=False,
        unique=True
    )

    duration_minutes = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    categories = db.Column(db.JSON, nullable=False)
    bloom_distribution = db.Column(db.JSON, nullable=True)


# =====================================================
# QUESTIONS
# =====================================================
class Question(db.Model):
    __tablename__ = 'tbl_questions'

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_courses.id'),
        nullable=False
    )

    topic_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_topics.id'),
        nullable=False
    )

    text = db.Column(db.Text, nullable=False)
    mark_value = db.Column(db.Integer, nullable=False)
    bloom_level = db.Column(db.String(32), nullable=False)
    difficulty = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, default=True)


# =====================================================
# GENERATED PAPERS
# =====================================================
class GeneratedPaper(db.Model):
    __tablename__ = 'tbl_generated_papers'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, nullable=False)
    template_id = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    generated_by = db.Column(
        db.Integer,
        db.ForeignKey('tbl_faculty.id'),
        nullable=False
    )

    co_weightages_snapshot = db.Column(db.JSON, nullable=False)

    questions = db.relationship(
        'GeneratedPaperQuestion',
        backref='paper',
        cascade='all,delete',
        lazy=True
    )


class GeneratedPaperQuestion(db.Model):
    __tablename__ = 'tbl_generated_paper_questions'

    id = db.Column(db.Integer, primary_key=True)

    paper_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_generated_papers.id'),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey('tbl_questions.id'),
        nullable=False
    )

    order = db.Column(db.Integer, nullable=False)
    mark_value = db.Column(db.Integer, nullable=False)
    section_label = db.Column(db.String(64))
    co_satisfied = db.Column(db.String(32))
