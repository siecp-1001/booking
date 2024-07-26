from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import   user_appionmentview, user_dwatial,TeacherSchedulesAPIView, AppointmentViewSet,CreateAppointmentView, LessonTimesForSubjectView,TimeListAPIView, LessonsForSubjectView, DateSlotViewSet,DurationListCreateAPIView, BookingViewSet, EnrollmentViewSet, index, user_dashboard,CenterViewSet,StudentViewSet,show_urls_view,CustomTokenObtainPairView, UserCreateView,LessonViewSet, teacher_list, teacher_detail, teacher_create, teacher_update, teacher_delete,SubjectViewSet, AvailableDaysView, TeachersForSubjectView, StudentCenterAPIView,DurationListCreateschudelerAPIView

router = DefaultRouter()
router.register(r'centers', CenterViewSet)
router.register(r'students', StudentViewSet)
router.register(r'dateslots', DateSlotViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'lessons',  LessonViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'duartion', DurationListCreateAPIView)
urlpatterns = [
    path('index/', index, name='index'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('', include(router.urls)),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('create-user/', UserCreateView.as_view(), name='create_user'),
    path('show-urls/', show_urls_view, name='show_urls'),
    path('teachers/', teacher_list, name='teacher-list'),
    path('teachers/<int:pk>/', teacher_detail, name='teacher-detail'),
    path('teachers/create/', teacher_create, name='teacher-create'),
    path('teachers/<int:pk>/update/', teacher_update, name='teacher-update'),
    path('teachers/<int:pk>/delete/', teacher_delete, name='teacher-delete'),
    path('userdaetial/<int:pk>/', user_dwatial, name='user-detail'),
    path('userappientmentview/<int:pk>/', user_appionmentview, name='appientmentview'),
    path('teacher-schedules/',  TeacherSchedulesAPIView.as_view(), name='teacher-schedules'),
    path('lessons-for-subject/<int:subject_id>/', LessonsForSubjectView.as_view(), name='lessons-for-subject'),
    path('subjects/<int:subject_id>/available-days/', AvailableDaysView.as_view(), name='available-days'),
    path('subjects/<int:subject_id>/teachers/', TeachersForSubjectView.as_view(), name='teachers-for-subject'),
    path('lesson-times-for-subject/<int:teacher_id>/<int:subject_id>/', LessonTimesForSubjectView.as_view(), name='lesson-times-for-subject'),
    path('duration-times-for-subject/<int:teacher_id>/', DurationListCreateschudelerAPIView.as_view(), name='duration-times-for-subject'),
    path('times-for-subject/<int:teacher_id>/',TimeListAPIView.as_view(), name='times-for-subject'),
    path('create_apointmnet/<int:teacher_id>/',CreateAppointmentView.as_view(), name='create_apointmnet'),
    path('student/center/', StudentCenterAPIView.as_view(), name='student-center')

]


