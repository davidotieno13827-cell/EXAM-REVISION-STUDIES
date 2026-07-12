from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count
from django.apps import apps
from .models import Category, Video, Comment, NewsletterSubscriber, ScheduleEntry


class KisiiTVAdminSite(AdminSite):
    site_header = 'Kisii TV Administration'
    site_title = 'Kisii TV Admin'
    index_title = 'Content Management Dashboard'
    index_template = 'admin/index.html'
    login_template = 'admin/login.html'
    
    def index(self, request, extra_context=None):
        """Custom admin index with content statistics."""
        extra_context = extra_context or {}
        
        # Collect statistics
        extra_context['stats'] = {
            'total_videos': Video.objects.count(),
            'videos_live': Video.objects.filter(is_live=True).count(),
            'featured_videos': Video.objects.filter(is_featured=True).count(),
            'total_comments': Comment.objects.count(),
            'pending_comments': Comment.objects.filter(is_approved=False).count(),
            'total_categories': Category.objects.count(),
            'scheduled_programs': ScheduleEntry.objects.count(),
            'newsletter_subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
            'total_users': User.objects.count(),
        }
        
        return super().index(request, extra_context)


# Create custom admin site instance
kisii_admin_site = KisiiTVAdminSite(name='kisii_admin')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'order')
        }),
    )


kisii_admin_site.register(Category, CategoryAdmin)


class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'published_date', 'views', 'likes', 'is_featured', 'is_live']
    list_filter = ['category', 'is_featured', 'is_live', 'published_date']
    search_fields = ['title', 'description']
    list_editable = ['is_featured', 'is_live']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'likes', 'created_at', 'updated_at']
    ordering = ['-published_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        ('Media', {
            'fields': ('thumbnail', 'video_url', 'duration')
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_live', 'published_date')
        }),
        ('Statistics', {
            'fields': ('views', 'likes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


kisii_admin_site.register(Video, VideoAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'video', 'created_at', 'is_approved']
    list_editable = ['is_approved']
    list_filter = ['is_approved', 'created_at', 'video__category']
    search_fields = ['author_name', 'content', 'video__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('video', 'author_name', 'author_email', 'content')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, 'Selected comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, 'Selected comments disapproved.')
    disapprove_comments.short_description = "Disapprove selected comments"


kisii_admin_site.register(Comment, CommentAdmin)


class KisiiTVUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    def _delete_user_related_content(self, user):
        user.watchlist_items.all().delete()
        user.video_likes.all().delete()
        user.groups.clear()
        user.user_permissions.clear()
        LogEntry.objects.filter(user=user).delete()

        for app_label, model_name in [('otp_static', 'StaticDevice'), ('otp_totp', 'TOTPDevice')]:
            try:
                DeviceModel = apps.get_model(app_label, model_name)
            except LookupError:
                continue
            DeviceModel.objects.filter(user=user).delete()

    def delete_model(self, request, obj):
        with transaction.atomic():
            self._delete_user_related_content(obj)
            obj.delete()

    def delete_queryset(self, request, queryset):
        # Delete one user at a time inside a transaction to avoid SQLite
        # FOREIGN KEY constraint errors that can occur with bulk deletes.
        for user in queryset:
            with transaction.atomic():
                self._delete_user_related_content(user)
                user.delete()


kisii_admin_site.register(User, KisiiTVUserAdmin)

class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'start_time', 'duration_minutes', 'status', 'is_featured']
    list_filter = ['status', 'is_featured', 'category']
    list_editable = ['status', 'is_featured']
    search_fields = ['title', 'category__name']
    ordering = ['start_time', 'title']

    fieldsets = (
        ('Program Details', {
            'fields': ('title', 'category', 'start_time', 'duration_minutes', 'status')
        }),
        ('Display Options', {
            'fields': ('is_featured',)
        }),
    )


kisii_admin_site.register(ScheduleEntry, ScheduleEntryAdmin)


class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']
    
    fieldsets = (
        ('Email Information', {
            'fields': ('email', 'is_active')
        }),
        ('Subscription Details', {
            'fields': ('subscribed_at', 'verification_token'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscribers', 'deactivate_subscribers']
    
    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} subscribers activated.')
    activate_subscribers.short_description = "Activate selected subscribers"
    
    def deactivate_subscribers(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} subscribers deactivated.')
    deactivate_subscribers.short_description = "Deactivate selected subscribers"


kisii_admin_site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)


