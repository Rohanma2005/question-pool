from app.routes.courses import courses_bp, courses_api_bp
from app.routes.departments import departments_bp

def register_routes(app):
    ...
    app.register_blueprint(courses_bp)
    app.register_blueprint(courses_api_bp)
    app.register_blueprint(departments_bp)
