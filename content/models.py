from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Category(models.Model):
    """Categories for organizing content"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class (e.g., 'fas fa-newspaper')")
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['order', 'name']),
        ]
    
    def __str__(self):
        return self.name


class ScheduleEntry(models.Model):
    """Program schedule entries for the homepage lineup."""
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='schedule_entries')
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=20, choices=[('live', 'Live Now'), ('up_next', 'Up Next'), ('coming_soon', 'Coming Soon')], default='coming_soon')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']
        verbose_name_plural = 'Schedule Entries'
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return f"{self.title} at {self.start_time}"


class Video(models.Model):
    """Video/Episode content"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    video_url = models.URLField(help_text="URL to the video (YouTube, Vimeo, etc.)", blank=True, null=True)
    duration = models.IntegerField(default=0, help_text="Duration in seconds")
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_live = models.BooleanField(default=False)
    published_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_date']
        verbose_name_plural = "Videos"
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['published_date']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_live']),
            models.Index(fields=['-views', '-likes', '-published_date'], name='video_popular_idx'),
        ]
    
    def __str__(self):
        return self.title
    
    def increment_views(self):
        """Increment view count"""
        self.views += 1
        self.save(update_fields=['views'])
    
    @property
    def trending_score(self):
        """Calculate trending score based on views and recency"""
        import datetime
        days_old = (timezone.now() - self.published_date).days
        if days_old == 0:
            days_old = 1
        return self.views / (days_old ** 1.5)


class Comment(models.Model):
    """Comments on videos"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Comments"
        indexes = [
            models.Index(fields=['is_approved', '-created_at'], name='comment_approved_created_idx'),
            models.Index(fields=['video', '-created_at'], name='comment_video_created_idx'),
        ]
    
    def __str__(self):
        return f"Comment by {self.author_name} on {self.video.title}"


class NewsletterSubscriber(models.Model):
    """Newsletter subscribers"""
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    verification_token = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['subscribed_at']),
        ]
    
    def __str__(self):
        return f"{self.email} ({'Active' if self.is_active else 'Inactive'})"


class WatchlistItem(models.Model):
    """User watchlist entries."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_items')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='watchlist_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'video')
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user', '-added_at'], name='watchlist_user_added_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.video.title}"


class VideoLike(models.Model):
    """User likes for videos."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_likes')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'video')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='videolike_user_created_idx'),
            models.Index(fields=['video', '-created_at'], name='videolike_video_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.video.title}"


