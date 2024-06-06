from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver 
import datetime  
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
import secrets
import string
from datetime import date, timedelta
from django.utils.timezone import now
class UserAccountManager(BaseUserManager):
    def create_user(self, email, name, password=None, is_teacher=False, is_student=False, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email)
        if password is None:
            password = self.generate_password()
        user = self.model(email=email, name=name, is_teacher=is_teacher, is_student=is_student, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Send a welcome email with the password
        self.send_welcome_email(user, password)
        
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email=email, name=name, password=password, is_teacher=False, is_student=False)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user
    
    def send_welcome_email(self, user, password):
        subject = 'Welcome to Our Platform'
        message = f'Hi {user.name},\n\nThank you for registering at our platform. Here are your login details:\n\nEmail: {user.email}\nPassword: {password}\n\nPlease keep this information secure.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, email_from, recipient_list)
    def generate_password(self, length=12):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for i in range(length))
        return password   

class UserAccount(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False) # New field to indicate teacher status
    is_student = models.BooleanField(default=False)
    is_center = models.BooleanField(default=False)
    
    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return self.email


class Center(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='center_profile', null=True, blank=True)
   
    address = models.TextField()

    def __str__(self):
        return self.user.name

    
class Student(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    lastname = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='students', default=1)  # Temporary default
    created_at = models.DateTimeField(auto_now_add=True)
    delete_confirmed = models.BooleanField(default=False)
    def __str__(self):
        return self.user.name if self.user else 'No User'

    
class Teacher(models.Model):
  
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    
    lastname = models.CharField(max_length=255, default='', null=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
   
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='teachers', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.user.name} "


    
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teachers = models.ManyToManyField(Teacher, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class DateSlot(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='available_slots')
    time = models.TimeField(default=datetime.time(9, 0))
    available = models.BooleanField(default=True)

    
    def __str__(self):
        return f"{self.time} - {'Available' if self.available else 'Unavailable'}"


class DeleteRequest(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    requested_by = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Delete request for {self.student.user.username} by {self.requested_by.username}"
class Lesson(models.Model):
    day = models.CharField(max_length=50)
    max_students = models.IntegerField()
    times = models.ManyToManyField(DateSlot)
    teacher = models.ManyToManyField(Teacher)
    subject = models.ManyToManyField(Course)
    created_at = models.DateField(auto_now_add=True)
    duration_days = models.IntegerField(default=30)  # Duration in days from creation

    def days_until_end(self):
        end_date = self.created_at + timedelta(days=self.duration_days)
        delta = end_date - date.today()
        return max(delta.days, 0)  # Ensure it doesn't return negative days

    def __str__(self):
        subjects = ', '.join([str(subject) for subject in self.subject.all()])
        teachers = ', '.join([str(teacher) for teacher in self.teacher.all()])
        days_remaining = self.days_until_end()
        return f"{subjects} by {teachers} on {self.day} ({days_remaining} days remaining)"
    

class Appointment(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True)
    time_slot = models.ForeignKey(DateSlot, on_delete=models.CASCADE)
    duration = models.DurationField()

    def __str__(self):
        if self.lesson:
            days_remaining = self.lesson.days_until_end()
            return f"{self.user} - {self.center}- {self.subject} - {self.lesson.day} ({days_remaining} days remaining) - {self.time_slot}"
        else:
            return f"{self.user} - {self.center}- {self.subject} - No lesson - {self.time_slot}"

    @staticmethod
    def check_availability(time_slot, duration):
        end_time = time_slot.time + duration
        overlapping_appointments = Appointment.objects.filter(
            time_slot__teacher=time_slot.teacher,
            time_slot__time__lt=end_time,
            time_slot__time__gte=time_slot.time
        )
        return not overlapping_appointments.exists()
class Booking(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bookings')
    date_slot = models.ForeignKey(DateSlot, on_delete=models.CASCADE, related_name='bookings')

    def __str__(self):
        return f"{self.student.user.name} - {self.date_slot.teacher.user.name} - {self.date_slot.start_time}"



class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.user.name} - {self.course.title}"
    


@receiver(post_save, sender=UserAccount)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_teacher:
            Teacher.objects.create(user=instance)
        elif instance.is_student:
            Student.objects.create(user=instance)
        elif instance.is_center:
            Center.objects.create(user=instance)

@receiver(post_save, sender=UserAccount)
def save_user_profile(sender, instance, **kwargs):
    if instance.is_teacher:
        instance.teacher.save()
    elif instance.is_student:
        instance.student.save()
    elif instance.is_center:
        try:
            instance.center_profile.save()
        except Center.DoesNotExist:
            Center.objects.create(user=instance)


@receiver(post_save, sender=Appointment)
def update_date_slot_availability(sender, instance, created, **kwargs):
    if created:
        # Mark the time slot as unavailable when an appointment is created
        instance.time_slot.available = False
        instance.time_slot.save()

@receiver(pre_delete, sender=Appointment)
def restore_date_slot_availability(sender, instance, **kwargs):
    # Mark the time slot as available when an appointment is deleted
    instance.time_slot.available = True
    instance.time_slot.save()