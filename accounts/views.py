from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import DateSlot, Booking, Course,Enrollment, Center, Student,Teacher,Appointment,Lesson
from .serializers import DateSlotSerializer, BookingSerializer, EnrollmentSerializer, CenterSerializer, StudentSerializer, CustomTokenObtainPairSerializer, CustomUserCreateSerializer,TeacherSerializer,AppointmentSerializer,LessonSerializer,SubjectSerializer
from .permissions import IsStudentOrReadOnly,IsCenterUser
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

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Student.objects.all()
        if user.is_center:
            return Student.objects.filter(center__user=user)
        return Student.objects.none()

    def perform_create(self, serializer):
        serializer.save(center=self.request.user.center_profile)

    def perform_update(self, serializer):
        serializer.save(center=self.request.user.center_profile)

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


class StudentCenterAPIView(generics.RetrieveAPIView):
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.student.center
class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Delete success.'}, status=status.HTTP_204_NO_CONTENT)
    

 
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCenterUser])
def teacher_list(request):
    if request.user.is_staff:
        teachers = Teacher.objects.all()
    elif request.user.is_center:
        teachers = Teacher.objects.filter(center__user=request.user)
    else:
        teachers = Teacher.objects.none()

    serializer = TeacherSerializer(teachers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCenterUser])
def teacher_detail(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and request.user.is_center and teacher.center.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer = TeacherSerializer(teacher)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCenterUser])
def teacher_create(request):
    serializer = TeacherSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsCenterUser])
def teacher_update(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and request.user.is_center and teacher.center.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer = TeacherSerializer(teacher, data=request.data, partial=('PATCH' in request.method))
    if serializer.is_valid():
        serializer.save(center=request.user.center_profile)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsCenterUser])
def teacher_delete(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return Response({'detail': 'Teacher not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and request.user.is_center and teacher.center.user != request.user:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    teacher.delete()
    return Response({'detail': 'Delete success.'}, status=status.HTTP_204_NO_CONTENT)

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
    elif user.is_center:
        data = {
            "message": f"Hello {user.name}, welcome to the center dashboard",
            "dashboard_data": "centre-specific data here"
        }
    else:
        data = {
            "message": "User type is not recognized",
            "dashboard_data": "No specific data available"
        }

    return Response(data)




class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = SubjectSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Delete success.'}, status=status.HTTP_204_NO_CONTENT)


class AvailableDaysView(generics.GenericAPIView):
    def get(self, request, subject_id):
        # Query to filter appointments by subject_id and get distinct lesson days
        appointments = Appointment.objects.filter(subject_id=subject_id).values_list('lesson__day', flat=True).distinct()
        available_days = list(appointments)
        return Response(available_days)
class TeachersForSubjectView(generics.GenericAPIView):
    def get(self, request, subject_id):
        subject = Course.objects.get(id=subject_id)
        teachers = subject.teachers.all()
        serializer = TeacherSerializer(teachers, many=True)
        return Response(serializer.data)