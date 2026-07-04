from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Video, Category, WatchlistItem, VideoLike, NewsletterSubscriber, ScheduleEntry


class WatchlistAndLikeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='viewer', password='secret123')
        self.category = Category.objects.create(name='News', slug='news', icon='fas fa-newspaper')
        self.video = Video.objects.create(
            title='Morning Update',
            slug='morning-update',
            category=self.category,
            description='Latest news',
            video_url='https://www.youtube.com/watch?v=test123',
            duration=1800,
        )

    def test_user_can_toggle_watchlist(self):
        self.client.login(username='viewer', password='secret123')
        response = self.client.post(reverse('toggle_watchlist', args=[self.video.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(WatchlistItem.objects.filter(user=self.user, video=self.video).exists())

        response = self.client.post(reverse('toggle_watchlist', args=[self.video.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WatchlistItem.objects.filter(user=self.user, video=self.video).exists())

    def test_user_can_toggle_like(self):
        self.client.login(username='viewer', password='secret123')
        response = self.client.post(reverse('toggle_like', args=[self.video.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VideoLike.objects.filter(user=self.user, video=self.video).exists())
        self.video.refresh_from_db()
        self.assertEqual(self.video.likes, 1)

        response = self.client.post(reverse('toggle_like', args=[self.video.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(VideoLike.objects.filter(user=self.user, video=self.video).exists())
        self.video.refresh_from_db()
        self.assertEqual(self.video.likes, 0)


class NewsletterTests(TestCase):
    def test_subscribe_newsletter_creates_active_subscriber(self):
        response = self.client.post(reverse('subscribe_newsletter'), {'email': 'viewer@example.com'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='viewer@example.com', is_active=True).exists())


class AuthFlowTests(TestCase):
    def test_homepage_shows_trending_and_personalized_sections(self):
        category = Category.objects.create(name='Culture', slug='culture', icon='fas fa-podcast')
        featured_video = Video.objects.create(
            title='Featured Broadcast',
            slug='featured-broadcast',
            category=category,
            description='Featured content',
            video_url='https://www.youtube.com/watch?v=featured',
            duration=1800,
            is_featured=True,
            views=120,
        )
        related_video = Video.objects.create(
            title='Recommended Local Story',
            slug='recommended-local-story',
            category=category,
            description='For you content',
            video_url='https://www.youtube.com/watch?v=recommended',
            duration=1800,
            views=80,
        )

        response = self.client.get(reverse('video_detail', kwargs={'slug': featured_video.slug}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Now Trending')
        self.assertContains(response, 'Featured Player')
        self.assertContains(response, 'For You')
        self.assertContains(response, related_video.title)

    def test_homepage_shows_continue_watching_for_recently_viewed_videos(self):
        self.category = Category.objects.create(name='Sports', slug='sports', icon='fas fa-futbol')
        self.video = Video.objects.create(
            title='Match Highlights',
            slug='match-highlights',
            category=self.category,
            description='Highlights',
            video_url='https://www.youtube.com/watch?v=test456',
            duration=1200,
        )

        response = self.client.get(reverse('video_detail', kwargs={'slug': self.video.slug}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue Watching')
        self.assertContains(response, 'Match Highlights')

    def test_homepage_shows_continue_watching_for_authenticated_user(self):
        self.user = get_user_model().objects.create_user(username='historyviewer', password='secret123')
        self.category = Category.objects.create(name='Sports', slug='sports', icon='fas fa-futbol')
        self.video = Video.objects.create(
            title='Match Highlights',
            slug='match-highlights',
            category=self.category,
            description='Highlights',
            video_url='https://www.youtube.com/watch?v=test456',
            duration=1200,
        )
        VideoLike.objects.create(user=self.user, video=self.video)

        self.client.login(username='historyviewer', password='secret123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue Watching')

    def test_homepage_renders_database_schedule_entries(self):
        category = Category.objects.create(name='News', slug='news-schedule', icon='fas fa-newspaper')
        ScheduleEntry.objects.create(
            title='Evening Brief',
            category=category,
            start_time='19:00',
            duration_minutes=30,
            status='live',
        )

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evening Brief')
        self.assertContains(response, 'Live Now')

    def test_homepage_displays_most_liked_videos(self):
        self.category = Category.objects.create(name='Culture', slug='culture', icon='fas fa-podcast')
        liked_video = Video.objects.create(
            title='Community Voices',
            slug='community-voices',
            category=self.category,
            description='Most liked video',
            video_url='https://www.youtube.com/watch?v=test789',
            duration=2400,
            likes=8,
        )
        regular_video = Video.objects.create(
            title='Local Music',
            slug='local-music',
            category=self.category,
            description='Less liked video',
            video_url='https://www.youtube.com/watch?v=test101',
            duration=1800,
            likes=3,
        )

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Most Liked')
        self.assertContains(response, liked_video.title)
        self.assertContains(response, regular_video.title)

    def test_homepage_shows_live_banner_schedule_and_recommendations(self):
        category = Category.objects.create(name='News', slug='news', icon='fas fa-newspaper')
        live_video = Video.objects.create(
            title='Live Bulletin',
            slug='live-bulletin',
            category=category,
            description='Live stream',
            video_url='https://www.youtube.com/watch?v=live123',
            duration=1800,
            is_live=True,
            views=500,
        )
        liked_video = Video.objects.create(
            title='Morning Briefing',
            slug='morning-briefing',
            category=category,
            description='Liked content',
            video_url='https://www.youtube.com/watch?v=liked123',
            duration=1800,
            likes=10,
        )

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Live Now')
        self.assertContains(response, 'Today\'s Schedule')
        self.assertContains(response, 'Recommended for You')
        self.assertContains(response, live_video.title)
        self.assertContains(response, liked_video.title)

    def test_user_can_register_and_access_profile(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('register'), {
            'username': 'newviewer',
            'email': 'newviewer@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='newviewer').exists())

        self.client.login(username='newviewer', password='StrongPass123')
        profile_response = self.client.get(reverse('profile'))
        self.assertEqual(profile_response.status_code, 200)
