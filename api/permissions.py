"""
Custom permission classes for API endpoints
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class to check if user is an admin/staff member.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff
