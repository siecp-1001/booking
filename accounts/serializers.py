from djoser import serializers as djoser_serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DateSlot, Booking, Enrollment, Center, Student
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
User = get_user_model()

class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    password = serializers.CharField(write_only=True)

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "password", "is_teacher", "is_student")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['is_teacher'] = user.is_teacher
        token['is_student'] = user.is_student
        

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user type information to the response data
        data['is_teacher'] = self.user.is_teacher
        data['is_student'] = self.user.is_student
       

        return data
class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = ['id', 'name', 'address']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'user', 'center']
        depth = 1

class DateSlotSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = DateSlot
        fields = ['id', 'teacher', 'start_time', 'end_time', 'status']
        depth = 1  # To include related objects

    def get_status(self, obj):
        return 'unavailable' if Booking.objects.filter(date_slot=obj).exists() else 'available'

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
