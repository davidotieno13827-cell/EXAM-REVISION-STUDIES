"""
Admin initialization script to populate sample data
Run with: python manage.py shell < scripts/populate_sample_data.py
"""

from content.models import Category, Video
from django.utils import timezone

# Clear existing data
print("Clearing existing data...")
Category.objects.all().delete()
Video.objects.all().delete()

# Create categories
print("Creating categories...")
categories_data = [
    {
        'name': 'News',
        'slug': 'news',
        'description': 'Breaking news and current events from Kisii and beyond',
        'icon': 'fas fa-newspaper'
    },
    {
        'name': 'Sports',
        'slug': 'sports',
        'description': 'Sports coverage including local and international events',
        'icon': 'fas fa-futbol'
    },
    {
        'name': 'Entertainment',
        'slug': 'entertainment',
        'description': 'Entertainment, music, and lifestyle content',
        'icon': 'fas fa-film'
    },
    {
        'name': 'Politics',
        'slug': 'politics',
        'description': 'Political news and analysis',
        'icon': 'fas fa-landmark'
    },
    {
        'name': 'Business',
        'slug': 'business',
        'description': 'Business and market updates',
        'icon': 'fas fa-briefcase'
    },
    {
        'name': 'Education',
        'slug': 'education',
        'description': 'Educational programs and learning content',
        'icon': 'fas fa-graduation-cap'
    },
]

categories = {}
for i, cat_data in enumerate(categories_data):
    cat = Category.objects.create(**cat_data, order=i)
    categories[cat.slug] = cat
    print(f"  ✓ Created category: {cat.name}")

# Create sample videos
print("\nCreating sample videos...")
videos_data = [
    {
        'title': 'Morning News Digest - July 3, 2026',
        'slug': 'morning-news-july-3',
        'description': 'Latest news and updates from around Kisii region. Breaking stories, weather updates, and community announcements.',
        'category': categories['news'],
        'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
        'duration': 45,
        'is_featured': True,
        'is_live': True,
    },
    {
        'title': 'Local Football Championship Finals',
        'slug': 'local-football-championship',
        'description': 'Highlights from the local football championship finals featuring the best teams from Kisii County.',
        'category': categories['sports'],
        'video_url': 'https://www.youtube.com/embed/9bZkp7q19f0',
        'duration': 90,
        'is_featured': True,
        'is_live': False,
    },
    {
        'title': 'Entertainment Spotlight - Music Awards',
        'slug': 'entertainment-music-awards',
        'description': 'Coverage of the annual Kisii Music Awards celebrating local artists and talent.',
        'category': categories['entertainment'],
        'video_url': 'https://www.youtube.com/embed/jNQXAC9IVRw',
        'duration': 60,
        'is_featured': True,
        'is_live': False,
    },
    {
        'title': 'Business Report - Market Updates',
        'slug': 'business-market-updates',
        'description': 'Weekly business report covering market trends, commodity prices, and business opportunities.',
        'category': categories['business'],
        'video_url': 'https://www.youtube.com/embed/oavMtUWDBTM',
        'duration': 30,
        'is_featured': True,
        'is_live': False,
    },
    {
        'title': 'Education Series - Digital Learning',
        'slug': 'education-digital-learning',
        'description': 'Educational series on digital literacy and the importance of technology in modern education.',
        'category': categories['education'],
        'video_url': 'https://www.youtube.com/embed/kJQP7kiw9Fk',
        'duration': 45,
        'is_featured': False,
        'is_live': False,
    },
    {
        'title': 'Evening News Update',
        'slug': 'evening-news-update',
        'description': 'All the important news and events from today, wrapped up in our evening news update.',
        'category': categories['news'],
        'video_url': 'https://www.youtube.com/embed/IFr8Dv0H6YU',
        'duration': 40,
        'is_featured': False,
        'is_live': False,
    },
    {
        'title': 'Sports Analysis - Weekly Review',
        'slug': 'sports-weekly-review',
        'description': 'In-depth analysis of the week\'s sports events and upcoming tournaments.',
        'category': categories['sports'],
        'video_url': 'https://www.youtube.com/embed/2uo4uU3NGGU',
        'duration': 50,
        'is_featured': False,
        'is_live': False,
    },
]

for video_data in videos_data:
    video = Video.objects.create(**video_data)
    print(f"  ✓ Created video: {video.title}")

print(f"\n✅ Successfully created {len(categories)} categories and {len(videos_data)} sample videos!")
print("\nYou can now visit the website to see the populated content.")
print("Admin panel: http://127.0.0.1:8000/admin/")
