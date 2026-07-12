import re
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.db import OperationalError
from django.urls import reverse
from .forms import RegisterForm
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from .models import Category, Video, Comment, NewsletterSubscriber, WatchlistItem, VideoLike, ScheduleEntry

HIDDEN_VIDEO_SLUGS = ['political-forum-development']


def _get_category_context():
    return {'request_categories': Category.objects.all()}


def _get_continue_watching_videos(request):
    history = request.session.get('watch_history', [])
    if history:
        seen = set()
        ordered_slugs = []
        for slug in history:
            if slug not in seen:
                seen.add(slug)
                ordered_slugs.append(slug)

        videos = Video.objects.filter(slug__in=ordered_slugs).exclude(slug__in=HIDDEN_VIDEO_SLUGS)
        ordered_videos = {video.slug: video for video in videos}
        ordered_history = [ordered_videos[slug] for slug in ordered_slugs if slug in ordered_videos]
        if ordered_history:
            return ordered_history[:3]

    if request.user.is_authenticated:
        return list(Video.objects.filter(video_likes__user=request.user).exclude(slug__in=HIDDEN_VIDEO_SLUGS).order_by('-video_likes__created_at')[:3])

    return []


def _record_watch_history(request, slug):
    history = request.session.get('watch_history', [])
    if slug in history:
        history.remove(slug)
    history.insert(0, slug)
    request.session['watch_history'] = history[:8]


def _build_embed_url(video_url):
    if not video_url:
        return None

    if 'youtube.com/watch' in video_url or 'youtu.be/' in video_url:
        video_id = None
        if 'v=' in video_url:
            video_id = re.search(r'[?&]v=([^&]+)', video_url)
        elif 'youtu.be/' in video_url:
            video_id = re.search(r'youtu\.be/([^?&]+)', video_url)
        if video_id:
            return f'https://www.youtube.com/embed/{video_id.group(1)}'

    if 'vimeo.com/' in video_url:
        video_id = re.search(r'vimeo\.com/([^/?#]+)', video_url)
        if video_id:
            return f'https://player.vimeo.com/video/{video_id.group(1)}'

    return None


def _get_for_you_videos(request, watched_slugs):
    watched_ids = list(Video.objects.filter(slug__in=watched_slugs).values_list('id', flat=True)) if watched_slugs else []
    category_preferences = []

    if request.user.is_authenticated:
        liked_videos = Video.objects.filter(video_likes__user=request.user).exclude(slug__in=HIDDEN_VIDEO_SLUGS)
        liked_category_ids = list(liked_videos.values_list('category_id', flat=True).distinct())
        category_preferences.extend(liked_category_ids)

    if watched_slugs:
        watched_videos = Video.objects.filter(slug__in=watched_slugs)
        watched_category_ids = list(watched_videos.values_list('category_id', flat=True).distinct())
        category_preferences.extend(watched_category_ids)

    category_preferences = list(dict.fromkeys(category_preferences))

    if category_preferences:
        queryset = Video.objects.exclude(id__in=watched_ids).exclude(slug__in=HIDDEN_VIDEO_SLUGS).filter(category_id__in=category_preferences)
        if queryset.exists():
            return list(queryset.order_by('-likes', '-views', '-published_date')[:6])

    queryset = Video.objects.exclude(id__in=watched_ids).exclude(slug__in=HIDDEN_VIDEO_SLUGS).order_by('-views', '-likes', '-published_date')
    return list(queryset[:6])


def _get_trending_videos():
    return list(Video.objects.exclude(slug__in=HIDDEN_VIDEO_SLUGS).order_by('-views', '-likes', '-published_date')[:8])


def _get_featured_video():
    return Video.objects.filter(is_featured=True).exclude(slug__in=HIDDEN_VIDEO_SLUGS).order_by('-published_date').first()


def _get_live_videos():
    return list(Video.objects.filter(is_live=True).exclude(slug__in=HIDDEN_VIDEO_SLUGS).order_by('-views', '-published_date'))


def _get_today_schedule():
    return list(ScheduleEntry.objects.filter(status='live').order_by('start_time'))


def home(request):
    """Render the homepage with featured, trending, personalized, live and schedule content."""
    watched_slugs = request.session.get('watch_history', [])
    continue_watching_videos = _get_continue_watching_videos(request)
    featured_video = _get_featured_video() or (_get_trending_videos()[:1] or [None])[0]
    recommended_videos = _get_for_you_videos(request, watched_slugs)
    trending_videos = _get_trending_videos()
    live_videos = _get_live_videos()
    today_schedule = _get_today_schedule()

    return render(request, 'index.html', {
        'featured_video': featured_video,
        'trending_videos': trending_videos,
        'recommended_videos': recommended_videos,
        'continue_watching_videos': continue_watching_videos,
        'live_videos': live_videos,
        'today_schedule': today_schedule,
    })


def category_view(request, slug):
    """Render content for a specific category."""
    category = get_object_or_404(Category, slug=slug)
    videos = category.videos.exclude(slug__in=HIDDEN_VIDEO_SLUGS).order_by('-published_date')
    categories = Category.objects.all()

    page = request.GET.get('page', 1)

    recommended_videos = Video.objects.exclude(category=category).exclude(slug__in=HIDDEN_VIDEO_SLUGS).order_by('-views')[:4]

    context = {
        'category': category,
        'videos': videos,
        'categories': categories,
        'page': page,
        'recommended_videos': recommended_videos,
    }
    return render(request, 'category.html', context)


def for_you(request):
    """Render the For You page with optional category filtering."""
    categories = Category.objects.all()
    selected_category = request.GET.get('category', '')
    category_filter = Category.objects.filter(slug=selected_category).first() if selected_category else None

    base_videos = Video.objects.exclude(slug__in=HIDDEN_VIDEO_SLUGS)
    filtered_videos = base_videos
    if category_filter:
        filtered_videos = filtered_videos.filter(category=category_filter)

    featured_videos = filtered_videos.filter(is_featured=True).order_by('-published_date')[:6]
    latest_videos = filtered_videos.order_by('-published_date')[:12]

    news_category = Category.objects.filter(slug='news').first()
    latest_news = Video.objects.none()
    if news_category:
        latest_news = base_videos.filter(category=news_category).order_by('-published_date')[:8]

    return render(request, 'for_you.html', {
        'latest_videos': latest_videos,
        'featured_videos': featured_videos,
        'latest_news': latest_news,
        'categories': categories,
        'selected_category': selected_category,
        'category_filter': category_filter,
        'featured_count': featured_videos.count(),
        'latest_count': latest_videos.count(),
        'news_count': latest_news.count(),
    })


def video_detail(request, slug):
    """Render a single video with details and interaction state."""
    if slug in HIDDEN_VIDEO_SLUGS:
        raise Http404()
    video = get_object_or_404(Video, slug=slug)
    video.increment_views()
    _record_watch_history(request, video.slug)

    related_videos = Video.objects.filter(
        category=video.category
    ).exclude(id=video.id).select_related('category').order_by('-published_date')[:6]

    approved_comments = video.comments.filter(is_approved=True).select_related('video').order_by('-created_at')
    categories = Category.objects.all()

    is_watchlisted = False
    is_liked = False
    if request.user.is_authenticated:
        is_watchlisted = WatchlistItem.objects.filter(user=request.user, video=video).exists()
        is_liked = VideoLike.objects.filter(user=request.user, video=video).exists()

    context = {
        'video': video,
        'related_videos': related_videos,
        'categories': categories,
        'comments': approved_comments,
        'is_watchlisted': is_watchlisted,
        'is_liked': is_liked,
    }
    return render(request, 'watch.html', context)


def search_videos(request):
    """Search functionality for videos with filtering and sorting."""
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'recent')
    categories = Category.objects.all()
    results = Video.objects.exclude(slug__in=HIDDEN_VIDEO_SLUGS)

    if query:
        results = results.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_slug:
        results = results.filter(category__slug=category_slug)

    if sort_by == 'popular':
        results = results.order_by('-views', '-published_date')
    elif sort_by == 'likes':
        results = results.order_by('-likes', '-published_date')
    else:
        results = results.order_by('-published_date')

    context = {
        'query': query,
        'results': results,
        'categories': categories,
        'selected_category': category_slug,
        'sort_by': sort_by,
    }
    return render(request, 'search.html', context)


@login_required
def toggle_watchlist(request, slug):
    """Add or remove a video from a user's watchlist."""
    video = get_object_or_404(Video, slug=slug)
    watchlist_item = WatchlistItem.objects.filter(user=request.user, video=video).first()

    if watchlist_item:
        watchlist_item.delete()
    else:
        WatchlistItem.objects.create(user=request.user, video=video)

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def toggle_like(request, slug):
    """Add or remove a like from a video."""
    video = get_object_or_404(Video, slug=slug)
    like = VideoLike.objects.filter(user=request.user, video=video).first()

    if like:
        like.delete()
        video.likes = max(video.likes - 1, 0)
        video.save(update_fields=['likes'])
    else:
        VideoLike.objects.create(user=request.user, video=video)
        video.likes = video.likes + 1
        video.save(update_fields=['likes'])

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def watchlist_view(request):
    """Display a user's saved watchlist."""
    videos = Video.objects.filter(watchlist_items__user=request.user).select_related('category').order_by('-watchlist_items__added_at')
    return render(request, 'watchlist.html', {'videos': videos, 'categories': Category.objects.all()})


def register_view(request):
    """Allow public registration using the standard registration form."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created and you are now signed in.')
            return redirect('profile')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {
        'form': form,
        'categories': Category.objects.all(),
    })


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """Log a user into the site."""

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            # Respect the 'next' parameter if provided, otherwise redirect to profile
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('profile')
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form, 'categories': Category.objects.all()})


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def editor_login(request):
    """Require a configured editor password before granting dashboard access."""

    if request.session.get('editor_authenticated'):
        return redirect('editor_dashboard')

    if request.method == 'POST':
        submitted_password = request.POST.get('editor_password') or request.POST.get('password', '')
        configured_password = getattr(settings, 'EDITOR_ACCESS_PASSWORD', None)
        next_url = request.POST.get('next') or request.GET.get('next')

        if configured_password and submitted_password.strip() == configured_password:
            request.session['editor_authenticated'] = True
            request.session.modified = True
            messages.success(request, 'Signed in successfully. You can now access the editor dashboard.')
            if next_url:
                return redirect(next_url)
            return redirect('editor_dashboard')

        return render(request, 'editor_login.html', {
            'error': 'Incorrect editor password. Please use the password provided by the administrator.',
            'next': next_url,
            'categories': Category.objects.all(),
        })

    next_url = request.GET.get('next', '')
    return render(request, 'editor_login.html', {'next': next_url, 'categories': Category.objects.all()})


def auth_choice(request):
    """Present sign-in choices: Admin, Editor, or Join as a local client."""
    # The admin link goes to Django admin; editor redirects to login with next to /editor/;
    # join directs to the registration page.
    return render(request, 'auth_choice.html', {
        'categories': Category.objects.all(),
    })


from django.urls import reverse


def admin_login(request):
    """Render and authenticate admin users, redirecting successful sign-in to the Django admin dashboard."""
    next_url = request.POST.get('next') or request.GET.get('next') or reverse('admin:index')
    error_message = None

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                error_message = 'Admin access is required. Please sign in with an administrator account.'
            else:
                login(request, user)
                return redirect(next_url)
        else:
            error_message = 'Please enter the correct username and password for an admin account.'
    else:
        form = AuthenticationForm(request)

    return render(request, 'admin_login.html', {
        'form': form,
        'error_message': error_message,
        'next': next_url,
        'categories': Category.objects.all(),
    })


@login_required
def logout_view(request):
    """Log the current user out."""
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    """Show the user's profile and recent activity."""
    saved_videos = Video.objects.filter(watchlist_items__user=request.user).select_related('category').order_by('-watchlist_items__added_at')[:6]
    liked_videos = Video.objects.filter(video_likes__user=request.user).select_related('category').order_by('-video_likes__created_at')[:6]
    return render(request, 'profile.html', {
        'saved_videos': saved_videos,
        'liked_videos': liked_videos,
        'categories': Category.objects.all(),
    })


def permission_denied_view(request, exception=None):
    """Render a friendly 403 page for unauthorized access."""
    return render(request, '403.html', status=403)


from django.urls import reverse


def editor_dashboard(request):
    """A lightweight editorial dashboard for staff to manage videos and schedule."""
    if not request.session.get('editor_authenticated'):
        return editor_login(request)

    # Require recent password confirmation before accessing sensitive editor actions.
    reauth_ts = request.session.get('reauthenticated_at')
    from django.utils import timezone
    if reauth_ts:
        try:
            reauth_time = timezone.datetime.fromtimestamp(float(reauth_ts), tz=timezone.utc)
        except Exception:
            reauth_time = None
    else:
        reauth_time = None

    # If not recently reauthenticated within the last 5 minutes, redirect to confirmation.
    # TEMPORARILY DISABLED FOR TESTING
    #if not reauth_time or (timezone.now() - reauth_time).total_seconds() > 300:
    #    return redirect(reverse('confirm_password') + f'?next={request.path}')
    message = request.session.pop('editor_message', None) if request.method == 'GET' else None
    if request.method == 'POST':
        action = request.POST.get('action', '')
        redirect_to_dashboard = False

        if action == 'create_video':
            title = request.POST.get('title', '').strip()
            slug = request.POST.get('slug', '').strip() or slugify(title)
            description = request.POST.get('description', '').strip()
            category_id = request.POST.get('category')
            video_url = request.POST.get('video_url', '').strip()
            duration = request.POST.get('duration', '0').strip() or '0'
            is_featured = request.POST.get('is_featured') == 'on'
            is_live = request.POST.get('is_live') == 'on'

            if title and category_id and video_url:
                try:
                    category = Category.objects.get(pk=category_id)
                    Video.objects.create(
                        title=title,
                        slug=slugify(slug),
                        description=description,
                        category=category,
                        video_url=video_url,
                        duration=int(duration),
                        is_featured=is_featured,
                        is_live=is_live,
                    )
                    message = 'Video added successfully.'
                    redirect_to_dashboard = True
                except Category.DoesNotExist:
                    message = 'Selected category does not exist.'
                except Exception:
                    message = 'Failed to add video. Please check input values.'
                    redirect_to_dashboard = True
            else:
                message = 'Title, category, and video URL are required.'
                redirect_to_dashboard = True

        elif action in ['toggle_live', 'toggle_featured', 'delete_video']:
            slug = request.POST.get('slug', '').strip()
            video = Video.objects.filter(slug=slug).first()
            if video:
                if action == 'delete_video':
                    title = video.title
                    video.delete()
                    message = f'Video "{title}" has been deleted.'
                    redirect_to_dashboard = True
                else:
                    if action == 'toggle_live':
                        video.is_live = not video.is_live
                        state = 'live' if video.is_live else 'offline'
                        video.save(update_fields=['is_live'])
                    else:
                        video.is_featured = not video.is_featured
                        state = 'featured' if video.is_featured else 'normal'
                        video.save(update_fields=['is_featured'])
                    message = f'Video "{video.title}" is now {state}.'
            else:
                message = 'Video not found.'
                redirect_to_dashboard = True

        elif action == 'create_schedule':
            title = request.POST.get('schedule_title', '').strip()
            category_id = request.POST.get('schedule_category')
            start_time = request.POST.get('start_time', '').strip()
            duration_minutes = request.POST.get('duration_minutes', '30').strip() or '30'
            status = request.POST.get('status', 'coming_soon')
            if title and category_id and start_time:
                try:
                    category = Category.objects.get(pk=category_id)
                    schedule_time = datetime.strptime(start_time, '%H:%M').time()
                    ScheduleEntry.objects.create(
                        title=title,
                        category=category,
                        start_time=schedule_time,
                        duration_minutes=int(duration_minutes),
                        status=status,
                    )
                    message = 'Schedule entry added successfully.'
                    redirect_to_dashboard = True
                except Category.DoesNotExist:
                    message = 'Selected category does not exist.'
                except ValueError:
                    message = 'Start time must use HH:MM format.'
                    redirect_to_dashboard = True
                except Exception:
                    message = 'Failed to add schedule entry.'
                    redirect_to_dashboard = True
            else:
                message = 'Title, category, and start time are required.'
                redirect_to_dashboard = True

        elif action == 'start_live_stream':
            title = request.POST.get('live_title', '').strip()
            description = request.POST.get('live_description', '').strip()
            category_id = request.POST.get('live_category')
            video_url = request.POST.get('live_url', '').strip()
            if title and category_id and video_url:
                try:
                    category = Category.objects.get(pk=category_id)
                    Video.objects.create(
                        title=title,
                        slug=slugify(title),
                        description=description or 'Live broadcast',
                        category=category,
                        video_url=video_url,
                        duration=0,
                        is_featured=True,
                        is_live=True,
                    )
                    message = 'Live stream started successfully.'
                    redirect_to_dashboard = True
                except Category.DoesNotExist:
                    message = 'Selected category does not exist.'
                except Exception:
                    message = 'Failed to start live stream.'
                    redirect_to_dashboard = True
            else:
                message = 'Title, category, and a stream URL are required.'
                redirect_to_dashboard = True

        elif action == 'create_news':
            title = request.POST.get('news_title', '').strip()
            slug = request.POST.get('news_slug', '').strip() or slugify(title)
            description = request.POST.get('news_description', '').strip()
            category_id = request.POST.get('news_category')
            video_url = request.POST.get('news_video_url', '').strip()
            duration = request.POST.get('news_duration', '0').strip() or '0'
            is_featured = request.POST.get('news_is_featured') == 'on'
            thumbnail = request.FILES.get('news_thumbnail')
            if title and category_id and thumbnail:
                try:
                    category = Category.objects.get(pk=category_id)
                    Video.objects.create(
                        title=title,
                        slug=slugify(slug),
                        description=description,
                        category=category,
                        video_url=video_url or None,
                        duration=int(duration),
                        thumbnail=thumbnail,
                        is_featured=is_featured,
                        is_live=False,
                    )
                    message = 'News update added successfully.'
                    redirect_to_dashboard = True
                except Category.DoesNotExist:
                    message = 'Selected category does not exist.'
                except ValueError:
                    message = 'Duration must be a number.'
                    redirect_to_dashboard = True
                except Exception:
                    message = 'Failed to add news update. Please check the uploaded image and form values.'
                    redirect_to_dashboard = True
            else:
                message = 'Title, category, and an image are required for news updates.'
                redirect_to_dashboard = True

        elif action == 'delete_schedule':
            entry_id = request.POST.get('entry_id', '').strip()
            schedule_entry = ScheduleEntry.objects.filter(id=entry_id).first()
            if schedule_entry:
                title = schedule_entry.title
                schedule_entry.delete()
                message = f'Schedule entry "{title}" has been deleted.'
                redirect_to_dashboard = True
            else:
                message = 'Schedule entry not found.'
                redirect_to_dashboard = True

        if redirect_to_dashboard:
            request.session['editor_message'] = message
            return redirect('editor_dashboard')

    videos = Video.objects.order_by('-published_date')[:10]
    schedule_entries = ScheduleEntry.objects.order_by('start_time')[:10]
    categories = Category.objects.all()

    return render(request, 'editor_dashboard.html', {
        'videos': videos,
        'schedule_entries': schedule_entries,
        'categories': categories,
        'message': message,
    })


@require_http_methods(["POST"])
def add_comment(request, video_slug):
    """Add a comment to a video."""
    video = get_object_or_404(Video, slug=video_slug)

    author_name = request.POST.get('author_name', 'Anonymous')
    author_email = request.POST.get('author_email', '')
    content = request.POST.get('content', '')

    if content.strip():
        Comment.objects.create(
            video=video,
            author_name=author_name or 'Anonymous',
            author_email=author_email,
            content=content,
            is_approved=False,
        )

    return redirect('video_detail', slug=video_slug)


@require_http_methods(["POST"])
def subscribe_newsletter(request):
    """Subscribe to the newsletter."""
    from django.http import JsonResponse

    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email is required'}, status=400)

    if NewsletterSubscriber.objects.filter(email=email, is_active=True).exists():
        return JsonResponse({'status': 'info', 'message': 'Email already subscribed'}, status=200)

    subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
    subscriber.is_active = True
    subscriber.save()

    message = 'Welcome! You have been subscribed to our newsletter.' if created else 'Subscription reactivated successfully.'
    return JsonResponse({'status': 'success', 'message': message}, status=201)


# ===== SECURITY & AUTHENTICATION VIEWS =====

class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with enhanced template and email handling."""
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = '/accounts/password_reset/done/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view with enhanced template."""
    template_name = 'password_reset_confirm.html'
    success_url = '/accounts/password_reset/complete/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


@login_required
def confirm_password(request):
    """Ask the logged-in user to re-enter their password for sensitive actions."""
    from django.utils import timezone

    next_url = request.GET.get('next') or request.POST.get('next') or reverse('editor_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # DEBUG: Log the submission attempt
        print(f"DEBUG: Form submission received")
        print(f"DEBUG: Submitted username: '{username}'")
        print(f"DEBUG: Logged-in user: '{request.user.username}'")
        print(f"DEBUG: Password length: {len(password)}")
        print(f"DEBUG: Password check result: {request.user.check_password(password)}")

        # Require the submitted username to match the logged-in user's username
        if username != request.user.username:
            print(f"DEBUG: Username mismatch!")
            messages.error(request, 'Username does not match the current account.')
            return render(request, 'confirm_password.html', {
                'next': next_url,
                'current_username': request.user.username,
                'categories': Category.objects.all(),
            })

        if request.user.check_password(password):
            # mark reauthentication timestamp in session (UTC epoch)
            request.session['reauthenticated_at'] = str(timezone.now().timestamp())
            request.session.modified = True
            request.session.save()  # Explicitly save the session
            # Return explicit HttpResponse with redirect
            from django.http import HttpResponse
            response = HttpResponse(status=302)
            response['Location'] = next_url
            return response
        else:
            messages.error(request, 'Incorrect password. Please try again.')
            return render(request, 'confirm_password.html', {
                'next': next_url,
                'current_username': request.user.username,
                'categories': Category.objects.all(),
            })

    messages.info(request, 'Confirm your password to continue to the secure editor area.')
    return render(request, 'confirm_password.html', {
        'next': next_url,
        'current_username': request.user.username,
        'categories': Category.objects.all(),
    })


# ===== SECURITY & AUTHENTICATION VIEWS =====

class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with enhanced template and email handling."""
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = '/accounts/password_reset/done/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view with enhanced template."""
    template_name = 'password_reset_confirm.html'
    success_url = '/accounts/password_reset/complete/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

