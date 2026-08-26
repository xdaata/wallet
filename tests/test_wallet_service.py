import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def idempotency_header():
    return {"x-idempotency-key": str(uuid.uuid4())}


@pytest.mark.asyncio
async def test_full_wallet_lifecycle(idempotency_header):
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))

    testing_session_local = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db():
        async with testing_session_local() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    try:
        with patch("app.core.middleware.redis_client", mock_redis):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                user_id = uuid.uuid4().int % 100000

                # 1 - создание кошелька
                create_res = await ac.post(f"/wallets/?user_id={user_id}", json={"currency": "RUB"})
                assert create_res.status_code in (200, 201)
                wallet_id = create_res.json()["id"]

                # 2 - получение баланса
                get_res = await ac.get(f"/wallets/{wallet_id}")
                assert get_res.status_code == 200

                # 3 - пополнение баланса
                dep_res = await ac.post(
                    f"/wallets/{wallet_id}/deposit?amount=500.00",
                    headers=idempotency_header
                )
                assert dep_res.status_code == 200

                # 4 - повторный запрос с тем же ключом
                dup_res = await ac.post(
                    f"/wallets/{wallet_id}/deposit?amount=500.00",
                    headers=idempotency_header
                )
                assert dup_res.status_code == 200

                # 5 - несуществующий кошелек
                not_found_res = await ac.get("/wallets/999999")
                assert not_found_res.status_code == 404
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_wallet_withdraw_and_errors():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))

    testing_session_local = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db():
        async with testing_session_local() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    try:
        with patch("app.core.middleware.redis_client", mock_redis):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                user_id = uuid.uuid4().int % 100000

                # 1 - создание и первичный депозит
                c_res = await ac.post(f"/wallets/?user_id={user_id}", json={"currency": "RUB"})
                wallet_id = c_res.json()["id"]

                await ac.post(
                    f"/wallets/{wallet_id}/deposit?amount=1000.00",
                    headers={"x-idempotency-key": str(uuid.uuid4())}
                )

                # 2 - успешное снятие
                w_res = await ac.post(
                    f"/wallets/{wallet_id}/withdraw?amount=400.00",
                    headers={"x-idempotency-key": str(uuid.uuid4())}
                )
                assert w_res.status_code == 200

                # 3 - попытка снять больше баланса
                fail_w_res = await ac.post(
                    f"/wallets/{wallet_id}/withdraw?amount=5000.00",
                    headers={"x-idempotency-key": str(uuid.uuid4())}
                )
                assert fail_w_res.status_code in (400, 422)

                # 4 - негативная сумма
                neg_res = await ac.post(
                    f"/wallets/{wallet_id}/deposit?amount=-100.00",
                    headers={"x-idempotency-key": str(uuid.uuid4())}
                )
                assert neg_res.status_code in (400, 422)
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
