from rest_framework.permissions import BasePermission
from rest_framework import permissions
from django.dispatch import Signal
class IsStudentOrReadOnly(BasePermission):
  
    def has_permission(self, request, view):
        # Allow all safe methods (GET, HEAD, OPTIONS)
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Allow POST and PUT methods for authenticated users
        if request.user.is_authenticated and request.method in ('POST', 'PUT'):
            return True
        # Deny DELETE method for students
        if request.user.is_authenticated and request.method == 'DELETE':
            return not request.user.is_student
        return False

    def has_object_permission(self, request, view, obj):
        # Allow all safe methods
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Allow DELETE method for non-students
        if request.method == 'DELETE':
            return not request.user.is_student
        return obj.student.user == request.user


class IsCenterUser(permissions.BasePermission):
    """
    Custom permission to only allow staff users or users who belong to a specific center.
    """

    def has_permission(self, request, view):
        # Staff members have all permissions
        if request.user.is_staff:
            return True
        
        # Center users have permissions based on their center
        if request.user.is_center:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Staff members can access all objects
        if request.user.is_staff:
            return True
        
        # Center users can access objects belonging to their center
        if request.user.is_center and obj.center == request.user.center:
            return True

        return False
    

