import os
import sys
import django

sys.path.insert(0, r'c:\Users\Administrator\OneDrive\Desktop\KISIITV.CO.KE\kisiitv.co.ke')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from content.models import Category, Video, ScheduleEntry
from django.utils import timezone

# Get or create a category
category, _ = Category.objects.get_or_create(
    slug='news',
    defaults={
        'name': 'News',
        'description': 'News and updates',
        'icon': 'fas fa-newspaper',
        'order': 1
    }
)

# Create a test video
Video.objects.create(
    title='Test News Video',
    slug='test-news-video',
    description='This is a test video for the editor dashboard',
    category=category,
    video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    duration=300,
    is_featured=False,
    is_live=False,
)

# Create another featured video
Video.objects.create(
    title='Breaking News - Live Coverage',
    slug='breaking-news-live',
    description='Live coverage of breaking news events',
    category=category,
    video_url='https://www.youtube.com/watch?v=jNQXAC9IVRw',
    duration=0,
    is_featured=True,
    is_live=True,
)

# Create a schedule entry
ScheduleEntry.objects.create(
    title='Evening News Broadcast',
    category=category,
    start_time='18:00',
    duration_minutes=60,
    status='coming_soon',
)

print("✅ Test data created successfully!")
print(f"- Created 2 test videos in '{category.name}' category")
print("- Created 1 schedule entry")
