from django.contrib import admin
from .models import UserAccount,Student,DateSlot,Duration,Booking,Teacher,Enrollment,Course,Center,Lesson,Appointment
admin.site.register(Student)
admin.site.register(DateSlot)
admin.site.register(UserAccount)
admin.site.register(Booking)
admin.site.register(Teacher)
admin.site.register(Enrollment)
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Appointment)
admin.site.register(Center)
admin.site.register(Duration)