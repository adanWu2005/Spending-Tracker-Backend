"""
Custom throttling classes for API key-based rate limiting using Redis
"""
from rest_framework.throttling import BaseThrottle, UserRateThrottle
from django.core.cache import cache
from .models import APIKey


class APIKeyRateThrottle(BaseThrottle):
    """
    Rate limiting for API keys using Redis cache.
    Implements per-minute, per-hour, and per-day limits.
    """
    
    def get_cache_key(self, request, view):
        """Generate cache key for this API key"""
        if hasattr(request, 'auth') and isinstance(request.auth, APIKey):
            api_key = request.auth
            return f'throttle_apikey_{api_key.key}'
        return None
    
    def allow_request(self, request, view):
        """
        Check if the request should be throttled.
        Returns True if request should be allowed, False if throttled.
        """
        # Only throttle if API key authentication was used
        if not hasattr(request, 'auth') or not isinstance(request.auth, APIKey):
            return True  # Not using API key, let other throttles handle it
        
        api_key = request.auth
        cache_key = self.get_cache_key(request, view)
        
        if not cache_key:
            return True
        
        # Get rate limits from API key
        per_minute = api_key.rate_limit_per_minute
        per_hour = api_key.rate_limit_per_hour
        per_day = api_key.rate_limit_per_day
        
        # Check per-minute limit
        minute_key = f"{cache_key}_minute"
        minute_count = cache.get(minute_key, 0)
        if minute_count >= per_minute:
            return False  # Throttled
        cache.set(minute_key, minute_count + 1, timeout=60)  # 1 minute TTL
        
        # Check per-hour limit
        hour_key = f"{cache_key}_hour"
        hour_count = cache.get(hour_key, 0)
        if hour_count >= per_hour:
            return False  # Throttled
        cache.set(hour_key, hour_count + 1, timeout=3600)  # 1 hour TTL
        
        # Check per-day limit
        day_key = f"{cache_key}_day"
        day_count = cache.get(day_key, 0)
        if day_count >= per_day:
            return False  # Throttled
        cache.set(day_key, day_count + 1, timeout=86400)  # 24 hours TTL
        
        return True  # Allowed
    
    def wait(self):
        """Return wait time in seconds before next request is allowed"""
        # This is called when throttled, but we don't know which limit was hit
        # Return a conservative 60 seconds
        return 60


class APIKeyUserRateThrottle(UserRateThrottle):
    """
    Rate limiting that works with API key authentication.
    Uses the user associated with the API key for rate limiting.
    """
    
    def get_cache_key(self, request, view):
        """Generate cache key based on API key user"""
        if hasattr(request, 'auth') and isinstance(request.auth, APIKey):
            # Use the user associated with the API key
            user = request.auth.user
            if user.is_authenticated:
                ident = user.pk
            else:
                ident = self.get_ident(request)
            
            return self.cache_format % {
                'scope': self.scope,
                'ident': ident
            }
        
        # Fall back to default behavior for JWT authentication
        return super().get_cache_key(request, view)
