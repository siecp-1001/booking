from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

   
class UserAccountManager(BaseUserManager):
    def create_user(self, email, name, password=None, is_teacher=False, is_student=False, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, is_teacher=is_teacher, is_student=is_student, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email=email, name=name, password=password, is_teacher=False, is_student=False)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)  # New field to indicate teacher status
    is_student = models.BooleanField(default=False)
    

    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return self.email


class Teacher(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.name

class Center(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return self.name
    
class Student(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='students', default=1)  # Temporary default

    def __str__(self):
        return self.user.name

    
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teachers = models.ManyToManyField(Teacher, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class DateSlot(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='available_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.teacher.user.name} - {self.start_time} to {self.end_time}"

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