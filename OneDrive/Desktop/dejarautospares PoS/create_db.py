import os
import sys
import logging
from app import app, db
from app.models import User

# Set up professional logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def init_db():
    """Initializes the database and seeds the admin user."""
    
    # 1. Pre-flight check: Ensure environment is ready
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not admin_username or not admin_password:
        logging.error("Configuration Error: ADMIN_USERNAME and ADMIN_PASSWORD must be set in your .env file.")
        sys.exit(1)

    with app.app_context():
        try:
            # 2. Database Creation
            logging.info("Creating database tables...")
            db.create_all()
            logging.info("Tables created successfully.")
            
            # 3. Secure Admin Seeding
            if not User.query.filter_by(username=admin_username).first():
                admin = User(username=admin_username)
                # Ensure models.py uses generate_password_hash
                admin.set_password(admin_password) 
                db.session.add(admin)
                db.session.commit()
                logging.info(f"Admin user '{admin_username}' created successfully.")
            else:
                logging.info("Admin user already exists; skipping seeding.")
                
        except Exception as e:
            logging.error(f"Critical error during database initialization: {e}")
            sys.exit(1)

if __name__ == '__main__':
    init_db()