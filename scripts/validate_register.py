import os
import sys
import json
from pathlib import Path

# Ensure project root is on sys.path so `config` package can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from content.forms import RegisterForm

form = RegisterForm(data={
    'username': 'tom brady',
    'email': 'tombrady@gmail.com',
    'password1': '12345678',
    'password2': '12345678',
})

print('is_valid=', form.is_valid())
print(form.errors.as_json())
