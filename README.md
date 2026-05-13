# To-Do List API with Real-time Features

**Студентка:** Панченко Вікторія Володимирівна  
**Група:** КВ-52мп  
**Лабораторна робота:** №2 - Організація спільної роботи користувачів Web-додатка  

## Опис завдання
Розробити функції обміну даними між користувачами Web-додатка у реальному часі та адміністрування користувачами, використовуючи Django Channels та WebSocket.

## Посилання на звіт
[Звіт на Google Drive](https://docs.google.com/document/d/1LpK2VqNtr33U3zs6IWpVS_dqQLZ_eKUpJoijLDdHqBg/edit?usp=sharing)

## Real-time функції
- ✅ WebSocket з'єднання для всіх авторизованих користувачів
- ✅ Відстеження онлайн користувачів в реальному часі
- ✅ Миттєве відображення нових завдань
- ✅ Real-time оновлення та видалення завдань
- ✅ Система персональних сповіщень
- ✅ Адміністративна панель для моніторингу онлайн користувачів
- ✅ Логування активності користувачів

## Технології
- Python 3.13
- Django 4.2
- Django Channels 4.0
- Redis 7.0
- WebSocket
- Bootstrap 5

## Встановлення та запуск

### Вимоги
- Python 3.11+
- Redis Server

### Кроки встановлення

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
4. Запуск Redis:
```bash
# Ubuntu/Debian
sudo systemctl start redis-server

# macOS
brew services start redis

# Windows/Docker
docker run -d -p 6379:6379 redis:alpine
```
5. Міграції бази даних:
```bash
python manage.py migrate
python manage.py createsuperuser
```
6. Запуск сервера:
```bash
python manage.py runserver
```

## Використання

### Веб-інтерфейс
- Головна сторінка: http://127.0.0.1:8000/
- Real-time демо: http://127.0.0.1:8000/realtime-demo/
- Адмін панель: http://127.0.0.1:8000/admin-dashboard/
- Django Admin: http://127.0.0.1:8000/admin/

### API Endpoints
- `GET /api/realtime/online-users/` - Список онлайн користувачів
- `GET /api/realtime/activity/` - Активність користувачів
- `GET /api/realtime/notifications/` - Сповіщення користувача
- `GET /api/realtime/stats/` - Статистика онлайн користувачів

### WebSocket
- URL: `ws://127.0.0.1:8000/ws/realtime/`
- Автоматичне підключення для авторизованих користувачів
- Підтримка ping/pong для підтримки з’єднання

### Демонстрація
1. Відкрийте кілька вкладок браузера
2. Увійдіть різними користувачами
3. Перейдіть на сторінку Real-time Demo
4. Додайте завдання з призначенням користувача в одній вкладці
5. Спостерігайте за оновленнями в інших вкладках
6. Перевірте адміністративну панель для моніторингу онлайн користувачів