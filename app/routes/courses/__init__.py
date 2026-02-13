from .routes import courses_bp
from .api import courses_api_bp
from . import detail  # <-- IMPORTANT (registers route)

__all__ = ['courses_bp', 'courses_api_bp', ]
