from rest_framework.permissions import BasePermission

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
