# To-Do List API

**Студентка:** Панченко Вікторія Володимирівна  
**Група:** КВ-52мп  
**Лабораторна робота:** №1 - Розробка серверної частини Web-додатка  

## Опис завдання
Розробити серверну частину Web-додатку для системи коментарів з використанням Django та Django REST Framework.

## Посилання на звіт
[Звіт на Google Drive](https://docs.google.com/document/d/1cm9oZ1uognkn4AOTeoR1GKdhWPuN_nqCEyNa4QQ9amE/edit?usp=sharing)

## Встановлення та запуск

1. Клонування репозиторію:
```bash
git clone https://github.com/sWcherry/to-do-list-api.git
cd to-do-list-api
```
2. Створення віртуального середовища:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
3. Встановлення залежностей:
```bash
pip install -r requirements.txt
```
4. Міграції бази даних:
```bash
python manage.py migrate
python manage.py createsuperuser
```
5. Запуск сервера:
```bash
python manage.py runserver
```

## API Документація

http://127.0.0.1:8000/api/docs/

## Основні endpoints

- `POST /api/auth/register/` - Реєстрація
- `POST /api/auth/login/` - Вхід
- `GET /api/auth/profile/` - Перегляд профілю
- `PATCH /api/auth/profile/` - Часткове оновлення профілю
- `DELETE /api/auth/profile/` - Видалення профілю
- `GET /api/tasks/` - Список завдань
- `POST /api/tasks/create/` - Створення завдання
- `GET /api/tasks/{id}/` - Деталі завдання
- `PATCH /api/tasks/{id}/` - Часткове оновлення завдання
- `DELETE /api/tasks/{id}/` - Видалення завдання
- `GET /api/info/` - Інформація про додаток

## Технології

- Python 3.13
- Django 4.2
- Django REST Framework 3.14
- SQLite (база даних)
