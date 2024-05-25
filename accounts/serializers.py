from djoser import serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DateSlot, Booking, Enrollment
User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "password","is_teacher"," is_student")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class DateSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateSlot
        fields = ['id', 'teacher', 'start_time', 'end_time']
        depth = 1  # To include related objects

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