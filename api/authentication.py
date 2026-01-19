"""
Custom authentication classes for API key authentication
"""
from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from .models import APIKey
from django.utils import timezone


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for API key-based authentication.
    API keys are passed in the Authorization header as: "Api-Key <key>"
    """
    
    def authenticate(self, request):
        # Get API key from header
        api_key = self.get_api_key(request)
        
        if not api_key:
            return None  # No API key provided, let other auth methods try
        
        try:
            # Look up API key in database
            key_obj = APIKey.objects.select_related('user').get(key=api_key, is_active=True)
            
            # Check if key is expired
            if key_obj.is_expired():
                raise exceptions.AuthenticationFailed('API key has expired')
            
            # Update last used timestamp
            key_obj.last_used = timezone.now()
            key_obj.save(update_fields=['last_used'])
            
            # Return user and API key object
            return (key_obj.user, key_obj)
            
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def get_api_key(self, request):
        """
        Extract API key from request headers.
        Supports both "Api-Key <key>" and "Authorization: Api-Key <key>" formats
        """
        # Try Api-Key header first
        api_key = request.META.get('HTTP_API_KEY')
        if api_key:
            return api_key.strip()
        
        # Try Authorization header with Api-Key prefix
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Api-Key '):
            return auth_header.split(' ', 1)[1].strip()
        
        return None
