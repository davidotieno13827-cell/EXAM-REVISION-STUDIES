from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('register/', RedirectView.as_view(pattern_name='register', permanent=False)),
    path('', views.home, name='home'),
    path('editor/', views.editor_dashboard, name='editor_dashboard'),
    path('editor-login/', views.editor_login, name='editor_login'),
    path('for-you/', views.for_you, name='for_you'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('watch/<slug:slug>/', views.video_detail, name='video_detail'),
    path('search/', views.search_videos, name='search'),
    path('watch/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('watch/<slug:slug>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
    path('watch/<slug:slug>/like/', views.toggle_like, name='toggle_like'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('auth-choice/', views.auth_choice, name='auth_choice'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('newsletter/subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('newsletter/', views.home, name='newsletter'),
    path('security/confirm-password/', views.confirm_password, name='confirm_password'),
]