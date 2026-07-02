import sys
from flask_migrate import Migrate, init as alembic_init, revision as alembic_revision, migrate as alembic_migrate, upgrade as alembic_upgrade
from app import app, db

migrate = Migrate(app, db)

USAGE = '''Usage: python manage_migrations.py [init|migrate|revision|upgrade]

Commands:
  init       Initialize the migrations directory (alembic)
  migrate    Autogenerate a new migration (autogenerate)
  revision   Create an empty revision with message (pass message as second arg)
  upgrade    Apply migrations (upgrade head)
'''

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'init':
        alembic_init(directory='migrations')
        print('Initialized migrations directory.')
    elif cmd == 'migrate':
        # autogenerate
        alembic_migrate(message='autogenerate', directory='migrations')
        print('Generated migration (autogenerate).')
    elif cmd == 'revision':
        msg = sys.argv[2] if len(sys.argv) > 2 else 'manual'
        alembic_revision(message=msg, directory='migrations')
        print(f'Created revision: {msg}')
    elif cmd == 'upgrade':
        alembic_upgrade(directory='migrations')
        print('Upgraded database to head.')
    else:
        print('Unknown command')
        print(USAGE)
 