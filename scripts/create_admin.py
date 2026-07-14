import os
import sys
import django

# Ensure project root is on sys.path so Django can import the config package
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = 'bill rusell'
email = 'dosystems13827@gmail.com'
password = 'Qfy9rdyeJeremylin7!'

if User.objects.filter(username=username).exists():
    print('Admin user already exists')
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Admin user created')
