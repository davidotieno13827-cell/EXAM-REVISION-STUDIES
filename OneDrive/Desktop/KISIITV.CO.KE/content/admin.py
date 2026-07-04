from django.contrib import admin
from .models import Category, Video, Comment, NewsletterSubscriber, ScheduleEntry

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'order')
        }),
    )


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'published_date', 'views', 'likes', 'is_featured', 'is_live']
    list_filter = ['category', 'is_featured', 'is_live', 'published_date']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'likes', 'created_at', 'updated_at']
    
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


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'video', 'created_at', 'is_approved']
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


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'start_time', 'duration_minutes', 'status', 'is_featured']
    list_filter = ['status', 'is_featured', 'category']
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


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
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
