from djoser import serializers as djoser_serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DateSlot, Booking, Enrollment, Center, Student,Teacher
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
import secrets
import string
from django.utils import timezone
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
        token['is_teacher'] = user.is_teacher
        token['is_student'] = user.is_student
        token['is_center'] = user.is_center

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user type information to the response data
        data['is_teacher'] = self.user.is_teacher
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
        fields = ['id', 'user', 'center']
       
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user

      
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
        return "available" if obj.available else "unavailable" 
class TeacherSerializer(serializers.ModelSerializer):
    user =CustomUserCreateSerializer()
    center = serializers.PrimaryKeyRelatedField(queryset=Center.objects.all())
    time_slots = DateSlotSerializer(many=True, read_only=True)
    class Meta:
        model = Teacher
        fields = ['id', 'user', 'bio', 'role', 'center']


    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(**user_data)
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user

        instance.bio = validated_data.get('bio', instance.bio)
        instance.role = validated_data.get('role', instance.role)
        instance.center = validated_data.get('center', instance.center)
        instance.save()

        user.email = user_data.get('email', user.email)
        user.name = user_data.get('name', user.name)
        user.save()

        return instance
    


class DateSlotSerializer(serializers.ModelSerializer):
    teacher = serializers.StringRelatedField()

    class Meta:
        model = DateSlot
        fields = ['id', 'teacher', 'time', 'available', 'status']

    status = serializers.CharField(source='get_status', read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = "available" if instance.available else "unavailable"
        return representation





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
