# Wallet Service

Бэкенд-сервис кошелька на FastAPI с поддержкой транзакций и идемпотентности операций.

## Стек

Python 3.14, FastAPI, PostgreSQL, Async SQLAlchemy, Alembic, Redis, Docker, Pytest, Locust.

## Запуск

Приложение: `http://localhost:8000`  
Протестировать через Swagger UI: `http://localhost:8000/docs`

### Через Docker Compose
```bash
docker-compose up --build -d