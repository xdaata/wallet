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

Миграции Alembic применяются автоматически при старте контейнера `web`.
Вручную: `docker-compose exec web alembic upgrade head`.

## Тесты

```bash
pip install -r requirements.txt
pytest
```

Тест `tests/test_wallet.py` ходит в настоящую БД: перед ним нужно
`docker-compose up -d db redis` и `alembic upgrade head`. Остальные тесты идут на SQLite в памяти.

## Остановка

Остановить контейнеры:
```bash
docker-compose down
```

Остановить и очистить данные баз:
```bash
docker-compose down -v
```
