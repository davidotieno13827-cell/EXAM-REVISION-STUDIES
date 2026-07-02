import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import generate_csrf
project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / '.env')

instance_path = project_root / 'instance'
instance_path.mkdir(exist_ok=True)

app = Flask(__name__, instance_relative_config=True, instance_path=str(instance_path))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
# Security-related defaults
# Maximum upload size (bytes) - default 2MB, can be overridden via MAX_CONTENT_LENGTH env
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 2 * 1024 * 1024))
# Make session cookies HttpOnly and set SameSite to Lax to mitigate CSRF via third-party sites
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
# If you are running behind HTTPS in production, set FORCE_HTTPS=true in the environment
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FORCE_HTTPS', 'false').lower() == 'true'


# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Expose csrf_token() function to templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Configure a basic Content Security Policy and security headers via Talisman
csp = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "https://cdn.jsdelivr.net"],
    "style-src": ["'self'", "https://cdn.jsdelivr.net", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https://cdn.jsdelivr.net"],
}
Talisman(app, content_security_policy=csp, force_https=app.config['SESSION_COOKIE_SECURE'])

# Rate limiting to mitigate brute-force attacks
storage_uri = os.getenv('RATE_LIMIT_STORAGE_URI', 'memory://')
limiter_enabled = os.getenv('FLASK_ENV', '').lower() != 'testing'
if storage_uri == 'memory://':
    app.logger.warning(
        'Using in-memory rate limiting storage; set RATE_LIMIT_STORAGE_URI to a Redis URI for production.'
    )
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    enabled=limiter_enabled,
)
limiter.init_app(app)

def _get_database_uri():
    database_url = os.getenv('DATABASE_URL')
    default_path = instance_path / 'app.db'
    if not database_url:
        return f"sqlite:///{default_path.resolve()}".replace('\\', '/')

    if database_url == 'sqlite:///:memory:':
        return database_url

    if database_url.startswith('sqlite:///'):
        db_path = database_url[10:]
        if db_path == '':
            return f"sqlite:///{default_path.resolve()}".replace('\\', '/')
        db_path = Path(db_path)
        if not db_path.is_absolute():
            absolute_path = (project_root / db_path).resolve()
            return f"sqlite:///{absolute_path}".replace('\\', '/')

    return database_url

app.config['SQLALCHEMY_DATABASE_URI'] = _get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'pos.login'

from app import models
from app.routes import pos
app.register_blueprint(pos.bp)
