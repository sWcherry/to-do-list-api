from django.db import models
from django.conf import settings

class Task(models.Model):
    """Модель завдання для списку справ"""
    
    STATUS_CHOICES = [
        ('Assigned', 'Призначено'),
        ('Completed', 'Завершено'),
    ]
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_tasks',
        verbose_name='Власник'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tasks',
        verbose_name='Призначено користувачу'
    )
    title = models.CharField(max_length=255, verbose_name='Назва')
    description = models.TextField(blank=True, verbose_name='Опис')
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='Assigned', 
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата оновлення')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Крайній термін')

class Meta:
        verbose_name = 'Завдання'
        verbose_name_plural = 'Завдання'
        ordering = ['-created_at']

def __str__(self):
    return f"{self.title} ({self.status})"