from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from tasks.models import Task

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Серіалізатор для реєстрації користувача"""
    
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'gender', 
                  'birth_date', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Паролі не співпадають.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class UserLoginSerializer(serializers.Serializer):
    """Серіалізатор для входу користувача"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])

        if not user:
            raise serializers.ValidationError("Невірний email або пароль.")

        if not user.is_active:
            raise serializers.ValidationError("Акаунт деактивовано.")

        data['user'] = user
        return data
    
class UserProfileSerializer(serializers.ModelSerializer):
    """Серіалізатор для профілю користувача"""

    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name', 
                  'gender', 'birth_date', 'avatar', 'created_at']
        read_only_fields = ['id', 'email', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    """Серіалізатор для завдань"""

    owner = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'owner', 'assigned_to', 'status', 'created_at', 'updated_at', 'deadline']
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']