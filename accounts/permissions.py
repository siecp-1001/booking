from rest_framework.permissions import BasePermission
from rest_framework import permissions
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
  

    def has_permission(self, request, view):
        # Ensure the user is authenticated and is a center user
        return request.user.is_authenticated and request.user.is_center

    def has_object_permission(self, request, view, obj):
        # Allow staff users to have full access
        if request.user.is_staff:
            return True
        # Check if the center user owns the object
        return obj.center.user == request.user