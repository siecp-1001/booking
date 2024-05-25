from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DateSlotViewSet, BookingViewSet, EnrollmentViewSet, index, user_dashboard

router = DefaultRouter()
router.register(r'dateslots', DateSlotViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'enrollments', EnrollmentViewSet)

urlpatterns = [
    path('index/', index, name='index'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('', include(router.urls)),
]
