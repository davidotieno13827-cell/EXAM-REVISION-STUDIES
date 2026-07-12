from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Video, Category, WatchlistItem, VideoLike, NewsletterSubscriber, ScheduleEntry


class AdminUserDeletionTests(TestCase):
    def test_bulk_delete_users_from_admin_does_not_error(self):
        admin_user = get_user_model().objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin_user)

        user_one = get_user_model().objects.create_user(username='user-one', password='StrongPass123!')
        user_two = get_user_model().objects.create_user(username='user-two', password='StrongPass123!')

        category = Category.objects.create(name='News', slug='news-admin', icon='fas fa-newspaper')
        video = Video.objects.create(
            title='Admin Test Video',
            slug='admin-test-video',
            category=category,
            description='Admin test video',
            video_url='https://www.youtube.com/watch?v=admintest',
            duration=600,
        )
        WatchlistItem.objects.create(user=user_one, video=video)
        VideoLike.objects.create(user=user_two, video=video)

        group = Group.objects.create(name='test-group')
        user_one.groups.add(group)

        permission = Permission.objects.first()
        if permission:
            user_one.user_permissions.add(permission)

        LogEntry.objects.create(
            user=user_one,
            content_type=ContentType.objects.get_for_model(User),
            object_id=user_one.pk,
            object_repr=str(user_one),
            action_flag=ADDITION,
        )

        response = self.client.post(
            reverse('admin:auth_user_changelist'),
            {
                'action': 'delete_selected',
                'post': 'yes',
                '_selected_action': [str(user_one.pk), str(user_two.pk)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk__in=[user_one.pk, user_two.pk]).exists())
        self.assertTrue(Group.objects.filter(pk=group.pk).exists())
        if permission:
            self.assertFalse(user_one.user_permissions.exists())
        self.assertFalse(LogEntry.objects.filter(user=user_one).exists())


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


class EditorAccessTests(TestCase):
    @override_settings(EDITOR_ACCESS_PASSWORD='TestEditorPass123!')
    def test_editor_login_accepts_configured_password(self):
        response = self.client.post(reverse('editor_login'), {
            'editor_password': 'TestEditorPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('editor_dashboard'))
        self.assertTrue(self.client.session.get('editor_authenticated'))

    def test_editor_dashboard_can_start_a_live_stream(self):
        category = Category.objects.create(name='Live', slug='live', icon='fas fa-broadcast-tower')
        session = self.client.session
        session['editor_authenticated'] = True
        session.save()

        response = self.client.post(reverse('editor_dashboard'), {
            'action': 'start_live_stream',
            'live_title': 'Live Broadcast',
            'live_description': 'Station live stream',
            'live_category': category.id,
            'live_url': 'https://www.youtube.com/watch?v=demo123',
        })

        self.assertEqual(response.status_code, 302)
        live_video = Video.objects.filter(is_live=True).latest('created_at')
        self.assertEqual(live_video.title, 'Live Broadcast')
        self.assertEqual(live_video.video_url, 'https://www.youtube.com/watch?v=demo123')
        self.assertTrue(live_video.is_live)


class AuthFlowTests(TestCase):
    def test_news_category_shows_requested_subcategories(self):
        Category.objects.create(name='News', slug='news', icon='fas fa-newspaper')
        Category.objects.create(name='Sports', slug='sports', icon='fas fa-futbol')

        response = self.client.get(reverse('category', kwargs={'slug': 'news'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sports')
        self.assertContains(response, 'Games')
        self.assertContains(response, 'Lifestyle')
        self.assertContains(response, 'Live Events')
        self.assertContains(response, 'Opinion & Blogs')

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
            'password1': 'Str0ngPass!123',
            'password2': 'Str0ngPass!123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='newviewer').exists())

        self.client.login(username='newviewer', password='StrongPass123')
        profile_response = self.client.get(reverse('profile'))
        self.assertEqual(profile_response.status_code, 200)
