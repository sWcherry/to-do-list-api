from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, F
from django.contrib.auth import get_user_model
from tasks.models import Task
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, TaskSerializer

User = get_user_model()

# Authentication views
class UserRegistrationView(generics.CreateAPIView):
    """Реєстрація нового користувача

    Створює новий акаунт користувача з обов'язковими полями:
    - email (унікальний, використовується для входу)
    - username
    - first_name
    - last_name
    - password (мінімум 8 символів)

    Опціональні поля:
    - gender (M, F, O)
    - birth_date

    Після успішної реєстрації повертає дані користувача та токен для аутентифікації.
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
class UserLoginView(generics.GenericAPIView):
    """Вхід користувача
    
    Дозволяє користувачу увійти в систему, використовуючи email та пароль.

    Після успішної аутентифікації повертає дані користувача та токен для подальших запитів.
    """

    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_200_OK)
    
class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """Профіль користувача

    Дозволяє користувачу:
    - Переглядати дані профілю
    - Оновлювати дані профілю (окрім email та created_at)
    - Видаляти акаунт користувача
    
    Захищено аутентифікацією, доступ тільки до власного профілю.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
# Task views
class TaskListView(generics.ListAPIView):
    """Список завдань з можливістю фільтрації та сортування

    Дозволяє користувачу переглядати список завдань, де він є:
    - власником 
    - призначеним виконавцем

    Підтримує фільтрацію за: 
    - статусом
    - власником (свої або інших)
    - виконавцем (свої, інших або непризначені)
    
    А також сортування за:
    - датою створення (за спаданням або зростанням)
    - терміном виконання (за зростанням)

    Захищено аутентифікацією, користувач бачить тільки свої та призначені йому завдання.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Всі завдання, де користувач або власник, або призначено йому
        user = self.request.user
        queryset = Task.objects.filter(
            Q(owner=user) | Q(assigned_to=user)  
        )

        # Фільтрація за статусом
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Фільтрація за власником завдання
        owner_param = self.request.query_params.get('owner')

        if owner_param == 'self':
            queryset = queryset.filter(owner=user)

            # Фільтрація за виконавцем завдання
            assigned_param = self.request.query_params.get('assigned_to')

            if assigned_param == 'self':
                queryset = queryset.filter(assigned_to=user)
            elif assigned_param == 'others':
                queryset = queryset.exclude(assigned_to=user).filter(assigned_to__isnull=False)
            elif assigned_param == 'unassigned':
                queryset = queryset.filter(assigned_to__isnull=True)

        elif owner_param == 'others':
            queryset = queryset.exclude(owner=user)
        
        # Сортування за датою створення або терміном виконання
        sort_param = self.request.query_params.get('sort')
        if sort_param == 'new':
            queryset = queryset.order_by('-created_at')
        elif sort_param == 'old':
            queryset = queryset.order_by('created_at')
        elif sort_param == 'deadline':
            queryset = queryset.order_by(F('deadline').asc(nulls_last=True))

        return queryset

class TaskCreateView(generics.CreateAPIView):
    """Створення нового завдання

    Дозволяє користувачу створити нове завдання, вказавши:
    - title (обов'язково)
    - description (необов'язково)
    - assigned_to (необов'язково, може бути призначено іншому користувачу або залишено незаповненим)
    - deadline (необов'язково)

    Після створення завдання, власник автоматично призначається як автор завдання. 
    Статус за замовчуванням - "Assigned".
    
    Захищено аутентифікацією, користувач може створювати тільки свої завдання.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Встановлюємо власника завдання як поточного користувача
        serializer.save(owner=self.request.user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Деталі, оновлення та видалення завдання

    Дозволяє користувачу переглядати, оновлювати та видаляти завдання.

    Захищено аутентифікацією, користувач може взаємодіяти тільки зі своїми та призначеними йому завданнями.

    Користувач може бачити завдання, якщо він:
    - власник
    - призначений виконавець

    Власник може оновлювати всі поля завдання (окрім owner, created_at, updated_at), 
    тоді як призначений виконавець – тільки статус.

    Видаляти завдання може тільки власник.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(owner=user) | Task.objects.filter(assigned_to=user)

    def perform_update(self, serializer):
        task = self.get_object()
        user = self.request.user

        if task.owner == user:
            # Власник оновлює все
            serializer.save()
        elif task.assigned_to == user:
            # Призначений користувач оновлює тільки статус
            serializer.save(status=serializer.validated_data.get('status', task.status))
        else:
            raise PermissionDenied("Ви не маєте прав на редагування цього завдання.")

    def perform_destroy(self, instance):
        if self.request.user != instance.owner:
            raise PermissionDenied("Ви не маєте прав на видалення цього завдання.")
        instance.delete()

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def app_info_view(request):
    """Інформація про додаток

    Повертає загальну інформацію про додаток, включаючи:
    - Назву додатку
    - Версію
    - Опис функціоналу
    - Логотип (URL)
    - Автора та контактні дані

    Доступно без аутентифікації.    
    """
    logo_url = request.build_absolute_uri(
        settings.STATIC_URL + 'images/logo.png'
    )

    return Response({
        'name': 'To-Do List',
        'version': '1.0.0',
        'description': 'Система управління завданнями у списку справ',
        'logo': logo_url,
        'features': [
            'Реєстрація та авторизація користувачів',
            'Перегляд завдань',
            'Додавання завдань',
            'Оновлення завдань',
            'Видалення завдань',
            'Управління статусами завдань',
            'Призначення завдань іншим користувачам',
        ],
        'author': 'Viktoriia Panchenko',
        'contact': '@rose_can_dy'
    })