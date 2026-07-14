import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

# Test accounts/emails we created
usernames = ['dave', 'tom_brady', 'tom_brady_2', 'fffff']
emails = ['davidotieno13827@gmail.com', 'tombrady@gmail.com', 'ffff@gmail.com']

for u in usernames:
    qs = User.objects.filter(username=u)
    if qs.exists():
        print('Deleting user:', u)
        qs.delete()

for e in emails:
    qs = User.objects.filter(email=e)
    if qs.exists():
        print('Deleting email:', e)
        qs.delete()

print('Cleanup complete')
