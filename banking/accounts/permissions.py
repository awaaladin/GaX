"""
Custom permissions for the banking application
"""
from rest_framework import permissions
from .models import APIKey
from django.utils import timezone


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsMerchant(permissions.BasePermission):
    """
    Permission to check if user is a merchant
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'merchant'
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'admin'
        )


class IsAPIKeyAuthenticated(permissions.BasePermission):
    """
    Permission to check if request has valid API key
    """

    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-Key', '')

        if not api_key:
            return False

        try:
            key_obj = APIKey.objects.get(
                key=api_key,
                is_active=True
            )

            # Check expiry
            if key_obj.expires_at and key_obj.expires_at < timezone.now():
                return False

            # Update last used
            key_obj.last_used_at = timezone.now()
            key_obj.save(update_fields=['last_used_at'])

            # Attach user to request
            request.user = key_obj.user

            return True

        except APIKey.DoesNotExist:
            return False
