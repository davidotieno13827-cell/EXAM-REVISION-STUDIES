import shutil
from pathlib import Path
from app import app, db

instance_dir = Path('instance')
db_path = instance_dir / 'app.db'
backup_path = instance_dir / 'app.db.bak'

if db_path.exists():
    print(f'Backing up {db_path} to {backup_path}')
    try:
        shutil.copy2(db_path, backup_path)
    except Exception as e:
        print('Backup failed:', e)

# Remove existing DB
try:
    if db_path.exists():
        db_path.unlink()
        print('Removed existing DB')
except Exception as e:
    print('Failed to remove DB:', e)

with app.app_context():
    db.create_all()
    print('Created new database schema.')
