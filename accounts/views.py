from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import DateSlot, Booking, Enrollment, Center, Student
from .serializers import DateSlotSerializer, BookingSerializer, EnrollmentSerializer, CenterSerializer, StudentSerializer, CustomTokenObtainPairSerializer, CustomUserCreateSerializer
from .permissions import IsStudentOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse
from .utils import list_urls
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework import generics

from djoser import utils
from django.conf import settings
from djoser import utils
from django.conf import settings
def show_urls_view(request):
    urls = list_urls()
    return JsonResponse({'urls': urls})
User = get_user_model()
class CenterViewSet(viewsets.ModelViewSet):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
    def confirm_delete(self, request, pk=None):
        student = self.get_object()
        student.delete()
        return Response({'status': 'student deleted'})

class DateSlotViewSet(viewsets.ModelViewSet):
    queryset = DateSlot.objects.all()
    serializer_class = DateSlotSerializer
    permission_classes = [IsAuthenticated]

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsStudentOrReadOnly]

    def get_queryset(self):
        queryset = Enrollment.objects.all()
        student_id = self.request.query_params.get('student_id', None)
        if student_id is not None:
            queryset = queryset.filter(student__id=student_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student)

    def destroy(self, request, *args, **kwargs):
        enrollment = self.get_object()
        if request.user.is_student:
            return Response({"detail": "You do not have permission to delete this enrollment."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer
# Function-based views
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def index(request):
    data = {
        "message": f"Hello {request.user.name}, welcome to your user area"
    }
    return Response(data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user

    if user.is_student:
        data = {
            "message": f"Hello {user.name}, welcome to the student dashboard",
            "dashboard_data": "Student-specific data here"
        }
    elif user.is_teacher:
        data = {
            "message": f"Hello {user.name}, welcome to the teacher dashboard",
            "dashboard_data": "Teacher-specific data here"
        }
    elif user.is_staff:
        data = {
            "message": f"Hello {user.name}, welcome to the admin dashboard",
            "dashboard_data": "Admin-specific data here"
        }
    else:
        data = {
            "message": "User type is not recognized",
            "dashboard_data": "No specific data available"
        }

    return Response(data)
