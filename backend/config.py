import os

class Config:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

    # CORS — comma-separated origins, or "*" to allow all
    _cors_raw = os.environ.get('CORS_ORIGINS', '*')
    CORS_ORIGINS = _cors_raw if _cors_raw == '*' else [o.strip() for o in _cors_raw.split(',')]

    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
