# app/__init__.py
from flask import Flask

from app.routes import register_routes
from .config import DevelopmentConfig
from .extensions import db, migrate
import os


def create_app(config_object=None):
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    app.config.from_object(config_object or DevelopmentConfig)
    
    # Set secret key for sessions
    app.config['SECRET_KEY'] = app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints (main routes for HTML views)
    from .routes.main import main_bp
    app.register_blueprint(main_bp)
    
    # Register API blueprints (for AJAX/API calls if needed)
    from .routes.api_auth import api_auth_bp
    app.register_blueprint(api_auth_bp, url_prefix='/api/auth')
    
    from .routes.api_departments import api_department_bp
    app.register_blueprint(api_department_bp, url_prefix='/api/departments')

    from .routes.api_faculty import api_faculty_bp
    app.register_blueprint(api_faculty_bp, url_prefix='/api/faculties')

    from .routes.api_programmes import api_programme_bp
    app.register_blueprint(api_programme_bp, url_prefix='/api/programmes')

    from app.routes import register_routes
    register_routes(app)


    

    @app.context_processor
    def inject_user():
        """Make user available in all templates"""
        from flask import session
        user = None
        if 'user_id' in session:
            from .models import SuperAdmin, Faculty
            if session.get('role') == 'super_admin':
                user = SuperAdmin.query.get(session['user_id'])
            else:
                user = Faculty.query.get(session['user_id'])
        return {'current_user': user}

    return app
