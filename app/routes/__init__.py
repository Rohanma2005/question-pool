from app.routes.courses import courses_bp, courses_api_bp
from app.routes.departments import departments_bp
from app.routes.faculty.fac_dashboard import fac_dashboard_bp
from app.routes.question_template.template_routes import templates_bp


def register_routes(app):
    ...
    app.register_blueprint(courses_bp)
    app.register_blueprint(courses_api_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(fac_dashboard_bp)
    app.register_blueprint(templates_bp)
    
