from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
import re


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full name (e.g. Tom Brady)'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username') or ''
        # Normalize: create a slug-like username (underscores instead of spaces)
        username_clean = username.strip()
        username_clean = re.sub(r'\s+', '_', username_clean)
        # Remove any disallowed characters and slugify for safety
        username_clean = re.sub(r"[^A-Za-z0-9@.\+\-\_]", '', username_clean)
        username_clean = slugify(username_clean).replace('-', '_')

        base = username_clean or 'user'
        candidate = base
        i = 1
        while User.objects.filter(username=candidate).exists():
            i += 1
            candidate = f"{base}_{i}"

        return candidate

    def save(self, commit=True):
        user = super().save(commit=False)
        # Save display name into first_name for admin display
        full_name = self.cleaned_data.get('full_name')
        if full_name:
            user.first_name = full_name
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user
