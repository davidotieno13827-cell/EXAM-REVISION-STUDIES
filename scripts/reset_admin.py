from django.contrib.auth import get_user_model
User = get_user_model()
username = 'billrussel'
new_password = 'Admin123!'
u, created = User.objects.get_or_create(username=username)
u.set_password(new_password)
u.is_active = True
u.is_staff = True
u.is_superuser = True
u.save()
if created:
    print('created superuser', username)
else:
    print('updated superuser', username)
