# app/utils.py
import os
from werkzeug.security import generate_password_hash
from app import db
from app.models import User

def update_admin_password(new_password):
    """Updates the admin password securely in the database."""
    # Ensure you are fetching the user correctly
    admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME')).first()
    
    if admin:
        admin.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return True
    return False