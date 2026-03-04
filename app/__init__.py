# app/__init__.py
from flask import Flask, session
from app.routes import register_routes
from .config import DevelopmentConfig
from .extensions import db, migrate
from datetime import timedelta
import os
import secrets


def create_app(config_object=None):
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    app.config.from_object(config_object or DevelopmentConfig)
    
    # Set secret key for sessions
    app.config['SECRET_KEY'] = app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Enable permanent sessions
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Make sessions permanent and generate CSRF token
    @app.before_request
    def make_session_permanent():
        session.permanent = True
        
        # Generate CSRF token for forms if not already present
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
    
    # Add cache control headers to prevent showing cached content from previous user
    @app.after_request
    def add_cache_control(response):
        # Don't cache HTML pages - force fresh content for each request
        if 'text/html' in response.headers.get('Content-Type', ''):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

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
