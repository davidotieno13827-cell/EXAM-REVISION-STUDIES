from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('watch/<slug:slug>/', views.video_detail, name='video_detail'),
    path('search/', views.search_videos, name='search'),
    path('watch/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('watch/<slug:slug>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
    path('watch/<slug:slug>/like/', views.toggle_like, name='toggle_like'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('newsletter/subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('newsletter/', views.home, name='newsletter'),
]