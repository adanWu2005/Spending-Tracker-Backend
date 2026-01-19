"""
Plaid API Rate Limiter
Implements rate limiting for Plaid API calls using Redis.
This matches the Rate Limiter component in the architecture diagram.
"""
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import time
import functools
from rest_framework.response import Response
from rest_framework import status


class PlaidRateLimiter:
    """
    Rate limiter for Plaid API calls using Redis.
    Implements token bucket algorithm for rate limiting.
    
    Plaid Rate Limits:
    - Sandbox: 500 requests/hour per client_id
    - Development: 500 requests/hour per client_id
    - Production: Varies by plan (typically 500-2000 requests/hour)
    """
    
    def __init__(self, requests_per_hour=500, requests_per_minute=50):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_hour: Maximum requests per hour (default: 500 for Plaid)
            requests_per_minute: Maximum requests per minute (default: 50 for burst protection)
        """
        self.requests_per_hour = requests_per_hour
        self.requests_per_minute = requests_per_minute
        self.cache_prefix = 'plaid_rate_limit'
    
    def _get_cache_key(self, identifier, window='hour'):
        """Generate cache key for rate limiting"""
        return f"{self.cache_prefix}:{identifier}:{window}"
    
    def _check_rate_limit(self, identifier):
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier (typically client_id or user_id)
            
        Returns:
            tuple: (is_allowed, remaining_requests, reset_time)
        """
        now = timezone.now()
        current_minute = int(now.timestamp() / 60)
        current_hour = int(now.timestamp() / 3600)
        
        # Check per-minute rate limit (burst protection)
        minute_key = self._get_cache_key(f"{identifier}:{current_minute}", 'minute')
        minute_count = cache.get(minute_key, 0)
        
        if minute_count >= self.requests_per_minute:
            # Calculate reset time (next minute)
            reset_time = (current_minute + 1) * 60
            return False, 0, reset_time
        
        # Check per-hour rate limit
        hour_key = self._get_cache_key(f"{identifier}:{current_hour}", 'hour')
        hour_count = cache.get(hour_key, 0)
        
        if hour_count >= self.requests_per_hour:
            # Calculate reset time (next hour)
            reset_time = (current_hour + 1) * 3600
            return False, 0, reset_time
        
        # Increment counters
        minute_ttl = 60  # 1 minute
        hour_ttl = 3600  # 1 hour
        
        cache.set(minute_key, minute_count + 1, minute_ttl)
        cache.set(hour_key, hour_count + 1, hour_ttl)
        
        remaining_hour = self.requests_per_hour - (hour_count + 1)
        remaining_minute = self.requests_per_minute - (minute_count + 1)
        remaining = min(remaining_hour, remaining_minute)
        
        # Reset time is the earliest of minute or hour reset
        reset_time = min((current_minute + 1) * 60, (current_hour + 1) * 3600)
        
        return True, remaining, reset_time
    
    def is_allowed(self, identifier):
        """
        Check if request is allowed and increment counter.
        
        Args:
            identifier: Unique identifier (client_id or user_id)
            
        Returns:
            tuple: (is_allowed, remaining_requests, reset_timestamp)
        """
        return self._check_rate_limit(identifier)
    
    def get_rate_limit_info(self, identifier):
        """
        Get current rate limit status without incrementing.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            dict: Rate limit information
        """
        now = timezone.now()
        current_minute = int(now.timestamp() / 60)
        current_hour = int(now.timestamp() / 3600)
        
        minute_key = self._get_cache_key(f"{identifier}:{current_minute}", 'minute')
        hour_key = self._get_cache_key(f"{identifier}:{current_hour}", 'hour')
        
        minute_count = cache.get(minute_key, 0)
        hour_count = cache.get(hour_key, 0)
        
        return {
            'minute_limit': self.requests_per_minute,
            'minute_remaining': max(0, self.requests_per_minute - minute_count),
            'minute_used': minute_count,
            'hour_limit': self.requests_per_hour,
            'hour_remaining': max(0, self.requests_per_hour - hour_count),
            'hour_used': hour_count,
        }


def plaid_rate_limit(requests_per_hour=500, requests_per_minute=50, identifier_func=None):
    """
    Decorator for rate limiting Plaid API calls.
    
    Args:
        requests_per_hour: Maximum requests per hour
        requests_per_minute: Maximum requests per minute
        identifier_func: Function to extract identifier from request/user
                         If None, uses client_id from environment
    
    Usage:
        @plaid_rate_limit(requests_per_hour=500)
        def my_plaid_function():
            ...
    """
    limiter = PlaidRateLimiter(requests_per_hour, requests_per_minute)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import os
            
            # Get identifier (client_id or user_id)
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                # Default: use Plaid client_id
                identifier = os.getenv('PLAID_CLIENT_ID', 'default')
            
            # Check rate limit
            is_allowed, remaining, reset_time = limiter.is_allowed(identifier)
            
            if not is_allowed:
                # Rate limit exceeded
                reset_datetime = timezone.datetime.fromtimestamp(reset_time, tz=timezone.utc)
                seconds_until_reset = int(reset_time - timezone.now().timestamp())
                
                error_response = {
                    'error': 'Plaid API rate limit exceeded',
                    'message': f'Too many requests. Please try again in {seconds_until_reset} seconds.',
                    'rate_limit': {
                        'limit': requests_per_hour,
                        'remaining': 0,
                        'reset_at': reset_datetime.isoformat(),
                        'reset_in_seconds': seconds_until_reset,
                    }
                }
                
                # Return Response object if this is a view function
                if hasattr(args[0], 'user') or (args and hasattr(args[0], 'data')):
                    # This is likely a Django view
                    return Response(error_response, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    # This is a service method, raise exception
                    raise Exception(f"Plaid API rate limit exceeded. Reset in {seconds_until_reset} seconds.")
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Re-raise original exception
                raise
        
        return wrapper
    return decorator
