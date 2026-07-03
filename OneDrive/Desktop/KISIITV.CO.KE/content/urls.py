from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), # The empty string '' represents the root homepage
]