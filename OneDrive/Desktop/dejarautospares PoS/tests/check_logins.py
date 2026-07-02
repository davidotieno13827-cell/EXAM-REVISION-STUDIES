from app import app, db
from app.models import User
import os
from create_db import init_db

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password123')

with app.app_context():
    # Seed admin via create_db helper
    try:
        init_db()
    except SystemExit:
        # init_db may call sys.exit if env not set; ignore here
        pass

    # Ensure a test user exists
    if not User.query.filter_by(username='test').first():
        u = User(username='test')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()

    client = app.test_client()

    def attempt_login(username, password):
        rv = client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
        text = rv.data.decode('utf-8')
        ok = f'Signed in as {username}' in text or 'Invalid username or password.' not in text
        return ok, rv.status_code, text[:400]

    admin_ok, admin_status, admin_preview = attempt_login(ADMIN_USERNAME, ADMIN_PASSWORD)
    print('Admin login:', admin_ok, admin_status)
    print(admin_preview)

    # logout
    client.get('/logout')

    test_ok, test_status, test_preview = attempt_login('test', 'pass')
    print('Test login:', test_ok, test_status)
    print(test_preview)
