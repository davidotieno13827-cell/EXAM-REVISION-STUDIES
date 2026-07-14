import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
from django.contrib.auth import get_user_model
from django.test import Client
from django.contrib.auth.hashers import make_password

django.setup()

User = get_user_model()

username = 'admin_test'
password = 'adminpassword'

user, created = User.objects.get_or_create(username=username, defaults={
    'email': 'admin_test@example.com',
    'is_superuser': True,
    'is_staff': True,
    'password': make_password(password),
})

if not created:
    user.password = make_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()

print('user exists:', user.username, user.email, user.is_superuser, user.is_staff)

client = Client()
logged_in = client.login(username=username, password=password)
print('login succeed:', logged_in)

resp = client.get('/admin/auth/user/')
print('status_code:', resp.status_code)
print('url:', resp.url)
print('content snippet:')
print(resp.content.decode('utf-8', errors='replace')[:3000])
