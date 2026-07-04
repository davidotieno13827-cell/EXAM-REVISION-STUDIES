import re

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import OperationalError
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from .models import Category, Video, Comment, NewsletterSubscriber, WatchlistItem, VideoLike, ScheduleEntry


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

        videos = Video.objects.filter(slug__in=ordered_slugs)
        ordered_videos = {video.slug: video for video in videos}
        ordered_history = [ordered_videos[slug] for slug in ordered_slugs if slug in ordered_videos]
        if ordered_history:
            return ordered_history[:3]

    if request.user.is_authenticated:
        return list(Video.objects.filter(video_likes__user=request.user).order_by('-video_likes__created_at')[:3])

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
        liked_videos = Video.objects.filter(video_likes__user=request.user)
        liked_category_ids = list(liked_videos.values_list('category_id', flat=True).distinct())
        category_preferences.extend(liked_category_ids)

    if watched_slugs:
        watched_videos = Video.objects.filter(slug__in=watched_slugs)
        watched_category_ids = list(watched_videos.values_list('category_id', flat=True).distinct())
        category_preferences.extend(watched_category_ids)

    category_preferences = list(dict.fromkeys(category_preferences))

    if category_preferences:
        queryset = Video.objects.exclude(id__in=watched_ids).filter(category_id__in=category_preferences)
        if queryset.exists():
            return list(queryset.order_by('-likes', '-views', '-published_date')[:6])

    queryset = Video.objects.exclude(id__in=watched_ids).order_by('-views', '-likes', '-published_date')
    return list(queryset[:6])


def home(request):
    """Render the homepage with featured, latest, and trending content."""
    featured_videos = Video.objects.filter(is_featured=True).order_by('-published_date')[:6]
    latest_videos = Video.objects.all().order_by('-published_date')[:8]

    trending_videos = sorted(
        Video.objects.all(),
        key=lambda x: x.trending_score,
        reverse=True,
    )[:5]

    categories = Category.objects.all()
    live_videos = Video.objects.filter(is_live=True)
    watchlist_videos = []
    continue_watching = _get_continue_watching_videos(request)

    if request.user.is_authenticated:
        watchlist_videos = Video.objects.filter(watchlist_items__user=request.user).order_by('-watchlist_items__added_at')[:4]

    recommended_videos = Video.objects.order_by('-views')[:6]
    most_liked_videos = Video.objects.order_by('-likes', '-views')[:6]
    watched_slugs = request.session.get('watch_history', [])
    for_you_videos = _get_for_you_videos(request, watched_slugs)
    featured_player_video = featured_videos.first() or latest_videos.first() or live_videos.first()
    featured_player_embed_url = _build_embed_url(featured_player_video.video_url) if featured_player_video else None
    live_now_video = live_videos.first() or featured_player_video
    try:
        schedule_entries = [
            {
                'time': entry.start_time.strftime('%H:%M'),
                'title': entry.title,
                'category': entry.category.name,
                'status': entry.get_status_display(),
            }
            for entry in ScheduleEntry.objects.select_related('category').all()[:6]
        ]
    except OperationalError:
        schedule_entries = []

    if not schedule_entries:
        schedule_entries = [
            {'time': '06:00', 'title': 'Morning Breakfast News', 'category': 'News', 'status': 'Live Now'},
            {'time': '08:00', 'title': 'Sports Roundup', 'category': 'Sports', 'status': 'Up Next'},
            {'time': '10:30', 'title': 'Community Talk Show', 'category': 'Talk Shows', 'status': 'Coming Soon'},
            {'time': '13:00', 'title': 'Business & Markets', 'category': 'News', 'status': 'Coming Soon'},
        ]

    context = {
        'featured_videos': featured_videos,
        'latest_videos': latest_videos,
        'trending_videos': trending_videos,
        'categories': categories,
        'live_videos': live_videos,
        'watchlist_videos': watchlist_videos,
        'recommended_videos': recommended_videos,
        'continue_watching': continue_watching,
        'most_liked_videos': most_liked_videos,
        'for_you_videos': for_you_videos,
        'featured_player_video': featured_player_video,
        'featured_player_embed_url': featured_player_embed_url,
        'live_now_video': live_now_video,
        'schedule_entries': schedule_entries,
    }
    return render(request, 'index.html', context)


def category_view(request, slug):
    """Render content for a specific category."""
    category = get_object_or_404(Category, slug=slug)
    videos = category.videos.all().order_by('-published_date')
    categories = Category.objects.all()

    page = request.GET.get('page', 1)

    recommended_videos = Video.objects.exclude(category=category).order_by('-views')[:4]

    context = {
        'category': category,
        'videos': videos,
        'categories': categories,
        'page': page,
        'recommended_videos': recommended_videos,
    }
    return render(request, 'category.html', context)


def video_detail(request, slug):
    """Render a single video with details and interaction state."""
    video = get_object_or_404(Video, slug=slug)
    video.increment_views()
    _record_watch_history(request, video.slug)

    related_videos = Video.objects.filter(
        category=video.category
    ).exclude(id=video.id).order_by('-published_date')[:6]

    approved_comments = video.comments.filter(is_approved=True).order_by('-created_at')
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
    results = Video.objects.all()

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
    videos = Video.objects.filter(watchlist_items__user=request.user).order_by('-watchlist_items__added_at')
    return render(request, 'watchlist.html', {'videos': videos, 'categories': Category.objects.all()})


def register_view(request):
    """Create a new user account."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form, 'categories': Category.objects.all()})


def login_view(request):
    """Log a user into the site."""
    from django.contrib.auth.forms import AuthenticationForm

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('profile')
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form, 'categories': Category.objects.all()})


@login_required
def logout_view(request):
    """Log the current user out."""
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    """Show the user's profile and recent activity."""
    saved_videos = Video.objects.filter(watchlist_items__user=request.user).order_by('-watchlist_items__added_at')[:6]
    liked_videos = Video.objects.filter(video_likes__user=request.user).order_by('-video_likes__created_at')[:6]
    return render(request, 'profile.html', {
        'saved_videos': saved_videos,
        'liked_videos': liked_videos,
        'categories': Category.objects.all(),
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