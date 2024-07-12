from djoser import serializers as djoser_serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DateSlot, Booking, Enrollment,Center, Student,Teacher,Appointment,Lesson,Course,Duration
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
import secrets
import string
from datetime import datetime, date, time, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.crypto import get_random_string
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)
    is_teacher = serializers.BooleanField(required=False, default=False)
    is_student = serializers.BooleanField(required=False, default=False)
    is_center = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'is_teacher', 'is_student', 'is_center', 'is_active', 'is_staff']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email address is required.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if password is None:
            password = self.generate_password()
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def generate_password(self, length=12):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for i in range(length))
        return password
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['is_active'] = user.is_active
        token['is_staff'] = user.is_staff
        token['is_teacher'] = user.is_teacher
        token['is_student'] = user.is_student
        token['is_center'] = user.is_center

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user type information to the response data
        data['is_teacher'] = self.user.is_teacher
        data['is_staff'] =self.user.is_staff
        data['is_student'] = self.user.is_student
        data['is_center'] = self.user.is_center

        return data

class CenterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Center
        fields = ['id', 'user', 'address']

class StudentSerializer(serializers.ModelSerializer):
    user =CustomUserCreateSerializer()
    center = serializers.PrimaryKeyRelatedField(queryset=Center.objects.all())
    class Meta:
        model = Student
        fields = ['id', 'user','lastname','phone', 'center','created_at', 'delete_confirmed']

    def create(self, validated_data):
        user_data = validated_data.pop('user')

        # Generate a random password
        random_password = get_random_string(length=8)
        user_data['password'] = random_password

        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)

        # Send email to the student
        subject = 'Welcome to Our School'
        message = (
            f"Dear {user.name},\n\n"
            f"Welcome to our school. We are excited to have you at {student.center}.\n\n"
            f"Your account has been created with the following details:\n"
            f"Email: {user.email}\n"
            f"Password: {random_password}\n\n"
            "Please log in and change your password as soon as possible.\n\n"
            "Best regards,\n"
            "The School Team"
        )
        from_email = settings.EMAIL_HOST_USER  # Use your sender email
        to_email = [user.email]
        send_mail(subject, message, from_email, to_email)

        return student

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user

        instance.lastname = validated_data.get('lastname', instance.lastname)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.center = validated_data.get('center', instance.center)
        instance.save()

        user.email = user_data.get('email', user.email)
        user.name = user_data.get('name', user.name)
        user.save()

        return instance


class DateSlotSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = DateSlot
        fields = '__all__'

    def get_status(self, obj):
        return "true" if obj.available else "false"

    def create(self, validated_data):
        # Remove the 'teacher' field from validated data if present
        validated_data.pop('teacher', None)
        return super().create(validated_data)

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'created_at']



class TeacherSerializer(serializers.ModelSerializer):
    user = CustomUserCreateSerializer()
    center_id = serializers.IntegerField(source='center.id', read_only=True)
    center = serializers.PrimaryKeyRelatedField(queryset=Center.objects.all())
    time_slots = DateSlotSerializer(many=True, read_only=True)
    courses = CourseSerializer(many=True, required=False)

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'lastname', 'phone', 'center', 'center_id', 'time_slots', 'courses', 'created_at']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        courses_data = validated_data.pop('courses', [])

        # Generate a random password
        password = self.generate_password()
        user_data['password'] = password

        user = User.objects.create(**user_data)
        teacher = Teacher.objects.create(user=user, **validated_data)

        for course_data in courses_data:
            course, created = Course.objects.get_or_create(**course_data)
            teacher.courses.add(course)

        # Send a welcome email with the password
        self.send_welcome_email(user, password)

        return teacher

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        courses_data = validated_data.pop('courses', None)
        user = instance.user

        instance.lastname = validated_data.get('lastname', instance.lastname)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.center = validated_data.get('center', instance.center)
        instance.save()

        if user_data:
            user.email = user_data.get('email', user.email)
            user.name = user_data.get('name', user.name)
            user.save()

        if courses_data is not None:
            instance.courses.clear()
            for course_data in courses_data:
                course, created = Course.objects.get_or_create(**course_data)
                instance.courses.add(course)

        return instance

    def send_welcome_email(self, user, password):
        subject = 'Welcome to Our Platform'
        message = f'Hi {user.name},\n\nThank you for registering as a teacher. You have been successfully added to our platform.\n\nYour login details are:\nEmail: {user.email}\nPassword: {password}\n\nPlease keep this information secure.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, email_from, recipient_list)

    def generate_password(self, length=12):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for i in range(length))
        return password
class TeacherNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name')  # Assuming 'name' is an attribute of the related UserAccount model


    class Meta:
        model = Teacher
        fields = ('name','id')
from rest_framework import serializers

class DateSlotSerializer(serializers.ModelSerializer):
    time = serializers.CharField(required=True)  # Ensure this field is required
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all(), required=True)  # Ensure this field is required

    class Meta:
        model = DateSlot
        fields = '__all__'

    def validate_status(self, value):
        if value.lower() not in ["true", "false"]:
            raise serializers.ValidationError("Status must be 'true' or 'false'.")
        return value

    def create(self, validated_data):
        status = validated_data.pop('status', None)

        if status is not None:
            validated_data['available'] = (status.lower() == "true")

        date_slot = DateSlot.objects.create(**validated_data)
        return date_slot

    def update(self, instance, validated_data):
        status = validated_data.pop('status', None)

        if status is not None:
            instance.available = (status.lower() == "true")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['status'] = "true" if instance.available else "false"
        return ret


class DurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Duration
        fields = ['id', 'length']

class LessonSerializer(serializers.ModelSerializer):
    times = DateSlotSerializer(many=True, read_only=True)
    teacher = TeacherSerializer(many=True, read_only=True)
    subject = CourseSerializer(many=True, read_only=True)
    center_id = serializers.IntegerField(write_only=True, required=True)
    duration = DurationSerializer(many=True, read_only=True)
    duration_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'max_students', 'startdate', 'end_date', 'times',
            'teacher', 'subject', 'created_at', 'duration_days',
            'duration', 'center_id', 'duration_ids'
        ]

    def validate(self, data):
        times_data = self.initial_data.get('times', [])
        teachers_data = self.initial_data.get('teacher', [])
        subjects_data = self.initial_data.get('subject', [])
        duration_ids = data.get('duration_ids', [])

        field_errors = {}

        if len(times_data) != len(set(times_data)):
            field_errors['times'] = "Duplicate times found."
        if len(subjects_data) != len(set(subjects_data)):
            field_errors['subject'] = "Duplicate subjects found."
        if len(duration_ids) != len(set(duration_ids)):
            field_errors['duration_ids'] = "Duplicate durations found."

        if teachers_data and not Teacher.objects.filter(id__in=teachers_data).exists():
            field_errors['teacher'] = "One or more provided teachers do not exist."
        if subjects_data and not Course.objects.filter(id__in=subjects_data).exists():
            field_errors['subject'] = "One or more provided subjects do not exist."

        for teacher_id in teachers_data:
            for subject_id in subjects_data:
                if self.instance:
                    # Skip current instance check during update to avoid false positive duplicate error
                    if Lesson.objects.filter(teacher__id=teacher_id, subject__id=subject_id).exclude(id=self.instance.id).exists():
                        field_errors['teacher_subject'] = f"A lesson with teacher ID {teacher_id} and subject ID {subject_id} already exists."
                else:
                    if Lesson.objects.filter(teacher__id=teacher_id, subject__id=subject_id).exists():
                        field_errors['teacher_subject'] = f"A lesson with teacher ID {teacher_id} and subject ID {subject_id} already exists."

        if field_errors:
            raise serializers.ValidationError(field_errors)

        return data

    def create(self, validated_data):
        times_data = self.initial_data.get('times', [])
        teachers_data = self.initial_data.get('teacher', [])
        subjects_data = self.initial_data.get('subject', [])
        duration_ids = validated_data.pop('duration_ids', [])
        center_id = validated_data.pop('center_id')

        lesson = Lesson.objects.create(center_id=center_id, **validated_data)

        if times_data and all(isinstance(item, int) for item in times_data):
            times = DateSlot.objects.filter(id__in=times_data)
            lesson.times.set(times)

        if teachers_data and all(isinstance(item, int) for item in teachers_data):
            for teacher_id in teachers_data:
                teacher = Teacher.objects.get(id=teacher_id)
                lesson.teacher.add(teacher)

        if subjects_data:
            for subject_id in subjects_data:
                subject = Course.objects.get(id=subject_id)
                if not lesson.subject.filter(id=subject_id).exists():
                    lesson.subject.add(subject)

        if duration_ids:
            for duration_id in duration_ids:
                duration = Duration.objects.get(id=duration_id)
                if not lesson.duration.filter(id=duration_id).exists():
                    lesson.duration.add(duration)

        return lesson

    def update(self, instance, validated_data):
        times_data = self.initial_data.get('times', [])
        teachers_data = self.initial_data.get('teacher', [])
        subjects_data = self.initial_data.get('subject', [])
        duration_ids = validated_data.pop('duration_ids', [])
        center_id = validated_data.get('center_id', instance.center_id)

        instance.max_students = validated_data.get('max_students', instance.max_students)
        instance.startdate = validated_data.get('startdate', instance.startdate)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.duration_days = validated_data.get('duration_days', instance.duration_days)
        instance.center_id = center_id

        if times_data and all(isinstance(item, int) for item in times_data):
            times = DateSlot.objects.filter(id__in=times_data)
            instance.times.set(times)

        if teachers_data and all(isinstance(item, int) for item in teachers_data):
            for teacher_id in teachers_data:
                teacher = Teacher.objects.get(id=teacher_id)
                instance.teacher.add(teacher)

        if subjects_data and all(isinstance(item, int) for item in subjects_data):
            for subject_id in subjects_data:
                subject = Course.objects.get(id=subject_id)
                instance.subject.add(subject)

        if duration_ids and all(isinstance(item, int) for item in duration_ids):
            for duration_id in duration_ids:
                duration = Duration.objects.get(id=duration_id)
                instance.duration.add(duration)

        instance.save()
        return instance

class AppointmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    center = serializers.PrimaryKeyRelatedField(queryset=Center.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), allow_null=True)
    time_slot = serializers.PrimaryKeyRelatedField(queryset=DateSlot.objects.all())
    lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'user', 'center','subject', 'lesson', 'time_slot', 'duration']

    def create(self, validated_data):
        user = validated_data.pop('user')
        center = validated_data.pop('center')
        subject = validated_data.get('subject')
        time_slot = validated_data.pop('time_slot')
        duration = validated_data.get('duration')

        # Ensure the DateSlot is available
        if not time_slot.available:
            raise serializers.ValidationError("The selected time slot is not available.")

        # Create the appointment
        appointment = Appointment.objects.create(
            user=user,
            center=center,
            subject=subject,
            time_slot=time_slot,
            duration=duration
        )

        # Mark the time slot as unavailable
        time_slot.available = False
        time_slot.save()

        return appointment

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.lesson:
            representation['lesson'] = LessonSerializer(instance.lesson).data
            # Add days remaining in the lesson
            representation['days_until_end'] = instance.lesson.days_until_end()
        else:
            representation['lesson'] = "No lesson"
            representation['days_until_end'] = None

        representation['user'] = CustomUserCreateSerializer(instance.user).data
        representation['center'] = CenterSerializer(instance.center).data
        representation['time_slot'] = DateSlotSerializer(instance.time_slot).data

        return representation

    def save(self, **kwargs):
        # When saving an appointment, also create the corresponding DateSlot if it doesn't exist
        if 'time_slot' in self.validated_data:
            time_slot_data = self.validated_data['time_slot']
            if isinstance(time_slot_data, dict) and 'teacher' in time_slot_data:
                teacher = time_slot_data['teacher']
                time = time_slot_data.get('time')
                if teacher and time:
                    date_slot, created = DateSlot.objects.get_or_create(teacher=teacher, time=time)
                    self.validated_data['time_slot'] = date_slot
        return super().save(**kwargs)

class SubjectSerializer(serializers.ModelSerializer):
    teachers = TeacherSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'student', 'date_slot']
        depth = 2  # To include related objects

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'enrolled_at']
        read_only_fields = ['enrolled_at', 'student']

    def validate(self, data):
        request = self.context.get('request')
        student = request.user.student
        course = data['course']
        if Enrollment.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError("The student is already enrolled in this course.")
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        student = request.user.student
        validated_data['student'] = student
        return super().create(validated_data)





class LessonDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['duration_days', 'created_at']


class DurationscSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['duration']

class LessonTimesSerializer(serializers.ModelSerializer):


    class Meta:
        model = Lesson
        fields = ['startdate', 'end_date']







class TimesAvailableSerializer(serializers.ModelSerializer):
    times = DateSlotSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ['times']




class CreateAppointmentSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    teacher = serializers.IntegerField(write_only=True)
    time_slot_id = serializers.IntegerField(write_only=True)
    subject_id = serializers.IntegerField(write_only=True)
    day = serializers.DateField()

    class Meta:
        model = Appointment
        fields = ['user_id', 'teacher', 'time_slot_id', 'subject_id', 'day', 'duration']

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        teacher_id = validated_data.pop('teacher')
        time_slot_id = validated_data.pop('time_slot_id')
        subject_id = validated_data.pop('subject_id')
        day = validated_data.pop('day')
        duration = validated_data['duration']

        user = User.objects.get(id=user_id)
        teacher = Teacher.objects.get(id=teacher_id)
        time_slot = DateSlot.objects.get(id=time_slot_id)
        subject = Course.objects.get(id=subject_id)

        # Check for availability
        if not Appointment.check_availability(teacher, day, time_slot, duration):
            raise serializers.ValidationError("This time slot is not available for the selected teacher.")

        appointment = Appointment.objects.create(
            user=user,
            teacher=teacher,
            center=teacher.center,
            subject=subject,
            time_slot=time_slot,
            day=day,
            duration=duration
        )

        return appointment