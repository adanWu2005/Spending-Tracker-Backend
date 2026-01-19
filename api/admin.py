from django.contrib import admin
from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin interface for API Key management"""
    list_display = ('name', 'user', 'is_active', 'is_expired', 'last_used', 'created_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('name', 'user__username', 'key')
    readonly_fields = ('key', 'created_at', 'last_used')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'key', 'is_active')
        }),
        ('Rate Limits', {
            'fields': ('rate_limit_per_minute', 'rate_limit_per_hour', 'rate_limit_per_day')
        }),
        ('Metadata', {
            'fields': ('created_at', 'expires_at', 'last_used')
        }),
    )
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
