from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.models import Task
from faker import Faker
import random
from datetime import datetime, timedelta

User = get_user_model()
fake = Faker('uk_UA')

class Command(BaseCommand):
    help = 'Populate database with test data'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Створення користувачів
        users = []
        for i in range(10):
            user = User.objects.create_user(
                email=fake.email(),
                username=fake.user_name(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=random.choice(['M', 'F', 'O']),
                birth_date=fake.date_of_birth(minimum_age=18, maximum_age=65),
                password='Test1234'  # тестовий пароль
            )
            users.append(user)
        
        self.stdout.write(f'{len(users)} users successfully created')

        # Створення завдань
        tasks = []
        for i in range(20):
            task = Task.objects.create(
                owner=random.choice(users),
                assigned_to=random.choice(users + [None]),
                title=fake.sentence(nb_words=6),
                description=fake.text(max_nb_chars=300),
                status=random.choice(['Assigned', 'Completed']),
                deadline=datetime.now() + timedelta(days=random.randint(0, 30)) if random.random() < 0.6 else None
            )
            tasks.append(task)
        
        self.stdout.write(f'{len(tasks)} tasks successfully created')
        self.stdout.write(
            self.style.SUCCESS('Successfully created test data')
        )