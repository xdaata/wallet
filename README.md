# Wallet Service

Бэкенд-сервис кошелька на FastAPI с поддержкой транзакций и идемпотентности операций.

## Стек

Python 3.14, FastAPI, PostgreSQL, Async SQLAlchemy, Alembic, Redis, Docker, Pytest, Locust.

## Интерфейс и API

* **Веб-интерфейс:** `http://localhost:8000`
* **Swagger UI (OpenAPI):** `http://localhost:8000/docs`

## Запуск

```bash
docker-compose up --build -d
```

## Остановка

Остановить контейнеры:
```bash
docker-compose down
```

Остановить и очистить данные баз:
```bash
docker-compose down -v
```