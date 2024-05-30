from djoser import serializers as djoser_serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DateSlot, Booking, Enrollment, Center, Student,Teacher
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
User = get_user_model()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
   
    is_teacher = serializers.BooleanField(default=False)
    is_student = serializers.BooleanField(default=False)
    is_center=serializers.BooleanField(default=False)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('email', 'name', 'password',  'is_teacher', 'is_student','is_center')

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
    status = serializers.SerializerMethodField()

    class Meta:
        model = DateSlot
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
