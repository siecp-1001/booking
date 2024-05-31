from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, DateSlotViewSet, BookingViewSet, EnrollmentViewSet, index, user_dashboard,CenterViewSet,StudentViewSet,show_urls_view,CustomTokenObtainPairView, UserCreateView,TeacherViewSet,LessonViewSet

router = DefaultRouter()
router.register(r'centers', CenterViewSet)
router.register(r'students', StudentViewSet)
router.register(r'dateslots', DateSlotViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'appointments', AppointmentViewSet)
urlpatterns = [
    path('index/', index, name='index'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('', include(router.urls)),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('create-user/', UserCreateView.as_view(), name='create_user'),
    path('show-urls/', show_urls_view, name='show_urls')
]
