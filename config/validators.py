import re
from django.core.exceptions import ValidationError


class ComplexPasswordValidator:
    """
    Validates that a password contains:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    
    def validate(self, password, user=None):
        errors = []

        if len(password) < 12:
            errors.append('Password must be at least 12 characters long.')

        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter (A-Z).')

        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter (a-z).')

        if not re.search(r'\d', password):
            errors.append('Password must contain at least one number (0-9).')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=[\]\;:\'"<>?,./]', password):
            errors.append('Password must contain at least one special character (!@#$%^&*...).')

        if errors:
            raise ValidationError(errors, code='password_too_simple')
    
    def get_help_text(self):
        return (
            'Your password must contain: at least 12 characters, an uppercase letter, a lowercase letter, a number and a special character.'
        )
