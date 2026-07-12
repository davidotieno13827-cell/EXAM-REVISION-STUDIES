from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from content import views as content_views
from content.admin import kisii_admin_site

urlpatterns = [
    path('admin/', kisii_admin_site.urls),
    # Custom auth URLs with enhanced security
    path('accounts/password_reset/', content_views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('accounts/password_reset/<uidb64>/<token>/', content_views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/password_reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('', include('content.urls')),
]

handler403 = 'content.views.permission_denied_view'

# This ensures Django can find and serve your uploaded videos and cover images
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)