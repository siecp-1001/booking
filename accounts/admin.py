from django.contrib import admin
from .models import UserAccount,Student,DateSlot,Booking,Teacher,Enrollment,Course
admin.site.register(Student)
admin.site.register(DateSlot)
admin.site.register(UserAccount)
admin.site.register(Booking)
admin.site.register(Teacher)
admin.site.register(Enrollment)
admin.site.register(Course)