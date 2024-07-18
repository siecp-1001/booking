from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import DateSlot, Booking, Course, Duration,DeleteRequest,Enrollment, Center, Student,Teacher,Appointment,Lesson
from .serializers import  UserDetailSerializer,CreateAppointmentSerializer, DateSlotSerializer,TimesAvailableSerializer,DurationscSerializer,LessonTimesSerializer,BookingSerializer,DurationSerializer, EnrollmentSerializer, CenterSerializer, StudentSerializer, CustomTokenObtainPairSerializer, CustomUserCreateSerializer, TeacherNameSerializer,TeacherSerializer,AppointmentSerializer,LessonSerializer,SubjectSerializer,LessonDurationSerializer
from .permissions import IsStudentOrReadOnly,IsCenterUser
from .signals import delete_request_created
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse
from .utils import list_urls
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.exceptions import NotFound
from djoser import utils
from django.conf import settings
from djoser import utils
from datetime import datetime
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
import logging
User = get_user_model()
logger = logging.getLogger(__name__)
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def request_delete(self, request, pk=None):
        student = self.get_object()
        delete_request, created = DeleteRequest.objects.get_or_create(student=student, requested_by=request.user)
        if created:
            delete_request_created.send(sender=self.__class__, delete_request=delete_request)
            return Response({'status': 'Delete request created, waiting for admin confirmation.'})
        return Response({'status': 'Delete request already exists, waiting for admin confirmation.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def confirm_delete(self, request, pk=None):
        try:
            delete_request = DeleteRequest.objects.get(student__id=pk, confirmed=False)
            delete_request.confirmed = True
            delete_request.save()
            student = delete_request.student
            student.delete()
            return Response({'status': 'Student deleted successfully.'})
        except DeleteRequest.DoesNotExist:
            return Response({'detail': 'No pending delete request for this student.'}, status=status.HTTP_400_BAD_REQUEST)
class DateSlotViewSet(viewsets.ModelViewSet):
    queryset = DateSlot.objects.all()
    serializer_class = DateSlotSerializer
    permission_classes = [IsAuthenticated]

class DurationListCreateAPIView(viewsets.ModelViewSet):
    queryset = Duration.objects.all()
    serializer_class = DurationSerializer
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Delete success.'}, status=status.HTTP_204_NO_CONTENT)



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
    queryset = Lesson.objects.all()  # Default queryset
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Assuming the user has a center_profile attribute linking to the Center model
        center = user.center_profile  # Adjust according to your actual model setup
        return Lesson.objects.filter(center=center)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

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
            "name":  user.student.center.user.name,
            "user_id": user.id,
            "phone":user.student.phone,
            "center_id": user.student.center.id,
            "center_name": user.student.center.user.name,
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
            "name":  user.name ,
            "email": user.email,
            "addres": user.center_profile.address,
            "phone": user.center_profile.phone,
            "dashboard_data": "centre-specific data here",
            "center_id": user.center_profile.id,
            "user_id": user.id
        }
    else:
        data = {
            "message": "User type is not recognized",
            "dashboard_data": "No specific data available"
        }

    return Response(data)




class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()  # Default queryset
    serializer_class = SubjectSerializer

    def get_queryset(self):
        user = self.request.user

        if hasattr(user, 'student'):
            center = user.student.center
        elif hasattr(user, 'teacher'):
            center = user.teacher.center
        elif hasattr(user, 'center_profile'):
            center = user.center_profile
        else:
            center = None

        if center is not None:
            return Course.objects.filter(center=center)
        else:
            return Course.objects.none()  # Return an empty queryset if the user has no associated center

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
        subject = get_object_or_404(Course, id=subject_id)
        teachers = subject.teachers.all()
        serializer = TeacherNameSerializer(teachers, many=True)
        return Response(serializer.data)


class LessonsForSubjectView(generics.GenericAPIView):
    serializer_class = LessonDurationSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, subject_id):
        try:
            course = Course.objects.get(id=subject_id)
        except Course.DoesNotExist:
            return Response({"detail": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Determine if the user is a teacher or a student and get the associated center
        if hasattr(user, 'teacher'):
            user_center = user.teacher.center
        elif hasattr(user, 'student'):
            user_center = user.student.center
        elif hasattr(user, 'center_profile'):
            user_center = user.center_profile
        else:
            return Response({"detail": "User does not belong to a center"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter lessons based on the subject and user's center
        lessons = Lesson.objects.filter(subject=course, center=user_center).distinct()
        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class LessonTimesForSubjectView(generics.GenericAPIView):
    serializer_class = LessonTimesSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, teacher_id, subject_id):
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response({"detail": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            subject = Course.objects.get(id=subject_id)
        except Course.DoesNotExist:
            return Response({"detail": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Determine if the user is a teacher, student, or center and get the associated center
        if hasattr(user, 'teacher'):
            user_center = user.teacher.center
        elif hasattr(user, 'student'):
            user_center = user.student.center
        elif hasattr(user, 'center_profile'):
            user_center = user.center_profile
        else:
            return Response({"detail": "User does not belong to a center"}, status=status.HTTP_400_BAD_REQUEST)

        # Get lessons based on teacher, subject, and user's center
        lessons = Lesson.objects.filter(teacher=teacher, subject=subject, center=user_center).distinct()
        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)







class DurationListCreateschudelerAPIView(generics.GenericAPIView):
    serializer_class = DurationscSerializer
    permission_classes=[IsAuthenticated]
    def get(self,request,teacher_id):
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
             return Response({"detail": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if hasattr(user, 'teacher'):
            user_center = user.teacher.center
        elif hasattr(user, 'student'):
            user_center = user.student.center
        elif hasattr(user, 'center_profile'):
            user_center = user.center_profile
        else:
            return Response({"detail": "User does not belong to a center"}, status=status.HTTP_400_BAD_REQUEST)


        courses= Course.objects.filter(teachers=teacher)

        lessons = Lesson.objects.filter(subject__in=courses, center=user_center).distinct()
        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Delete success.'}, status=status.HTTP_204_NO_CONTENT)




class TimeListAPIView(generics.GenericAPIView):
    serializer_class = TimesAvailableSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response({"detail": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if hasattr(user, 'teacher'):
            user_center = user.teacher.center
        elif hasattr(user, 'student'):
            user_center = user.student.center
        elif hasattr(user, 'center_profile'):
            user_center = user.center_profile
        else:
            return Response({"detail": "User does not belong to a center"}, status=status.HTTP_404_NOT_FOUND)

        courses = Course.objects.filter(teachers=teacher)
        lessons = Lesson.objects.filter(subject__in=courses, center=user_center).distinct()

        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TeacherSchedulesAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = self.request.user

            # Get the date from the request
            date_str = request.query_params.get('date')
            if date_str:
                try:
                    date = datetime.strptime(date_str, '%d/%m/%Y').date()
                except ValueError:
                    return Response({"detail": "Invalid date format. Use DD/MM/YYYY."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": "Date parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Determine the user type and get their associated center
            if hasattr(user, 'student'):
                center = user.student.center
                appointments = Appointment.objects.filter(user=user, day=date).prefetch_related('teacher__user', 'time_slot')
            elif hasattr(user, 'teacher'):
                center = user.teacher.center
                appointments = Appointment.objects.filter(teacher=user.teacher, day=date).prefetch_related('user', 'time_slot')
            elif hasattr(user, 'center_profile'):
                center = user.center_profile
                teachers = Teacher.objects.filter(center=center)
                appointments = Appointment.objects.filter(teacher__center=center, day=date).prefetch_related('user', 'teacher__user', 'time_slot')
            else:
                return Response({"detail": "User is not associated with any center."}, status=status.HTTP_404_NOT_FOUND)

            if center is None:
                return Response({"detail": "User is not associated with any center."}, status=status.HTTP_404_NOT_FOUND)

            data = []

            if hasattr(user, 'student'):
                teacher_dict = {}
                for appointment in appointments:
                    teacher_name = appointment.teacher.user.name
                    teacher_id = appointment.teacher.user.id
                    time = appointment.time_slot.time.strftime('%I:%M %p')

                    if teacher_id not in teacher_dict:
                        teacher_dict[teacher_id] = {
                            "id": teacher_id,
                            "teacher": teacher_name,
                            time: [{
                                "name": user.name,
                                "id": user.id
                            }]
                        }
                    else:
                        if time not in teacher_dict[teacher_id]:
                            teacher_dict[teacher_id][time] = []
                        teacher_dict[teacher_id][time].append({
                            "name": user.name,
                            "id": user.id
                        })
                data.extend(teacher_dict.values())


            elif hasattr(user, 'teacher'):
                schedule = {
                    "id": user.id,
                    "teacher": user.teacher.user.name,
                    "appointments": []
                }
                for appointment in appointments:
                    time = appointment.time_slot.time.strftime('%I:%M %p')

                    schedule["appointments"].append({

                        "time": time,
                        "student": {
                            "name": appointment.user.name,
                            "id": appointment.user.id
                        }
                    })
                data.append(schedule)

            elif hasattr(user, 'center_profile'):
                for teacher in teachers:
                    schedule = {
                        "id": teacher.id,
                        "teacher": teacher.user.name
                    }
                    teacher_appointments = appointments.filter(teacher=teacher)
                    for appointment in teacher_appointments:
                        time = appointment.time_slot.time.strftime('%I:%M %p')
                        if time not in schedule:
                            schedule[time] = []
                        schedule[time].append({
                            "name": appointment.user.name,
                            "id": appointment.user.id
                        })
                    data.append(schedule)

            return Response(data, status=status.HTTP_200_OK)

        except user.DoesNotExist:
            return Response({"detail": "User account not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


User = get_user_model()


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        try:
            user = self.queryset.get(pk=user_id)
            serializer = self.serializer_class(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class CreateAppointmentView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CreateAppointmentSerializer(data=request.data)
        if serializer.is_valid():
            appointment = serializer.save()
            return Response({
                "id": appointment.id,
                "user": appointment.user.id,
                "teacher": appointment.teacher.id,
                "center": appointment.center.id,
                "subject": appointment.subject.id,
                "time_slot": appointment.time_slot.id,
                "day": appointment.day,
                "duration": appointment.duration
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_dwatial(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        raise NotFound("User not found")

    if hasattr(user, 'student'):
        data = {
            "name": user.name,
            "user_id": user.id,
            "phone": user.student.phone,
            "email": user.email,
            "center_id": user.student.center.id,
            "center_name": user.student.center.user.name,
            "dashboard_data": "Student-specific data here"
        }
    elif hasattr(user, 'teacher'):
        data = {
            "message": f"Hello {user.name}, welcome to the teacher dashboard",
            "dashboard_data": "Teacher-specific data here"
        }
    elif user.is_staff:
        data = {
            "message": f"Hello {user.name}, welcome to the admin dashboard",
            "dashboard_data": "Admin-specific data here"
        }
    elif hasattr(user, 'center_profile'):
        data = {
            "name": user.name,
            "email": user.email,
            "address": user.center_profile.address,
            "phone": user.center_profile.phone,
            "dashboard_data": "Centre-specific data here",
            "center_id": user.center_profile.id,
            "user_id": user.id
        }
    else:
        data = {
            "message": "User type is not recognized",
            "dashboard_data": "No specific data available"
        }

    return Response(data)