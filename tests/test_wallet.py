import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_wallet_success(client: AsyncClient):
    response = await client.post("/wallets/?user_id=999", json={"currency": "RUB"})

    assert response.status_code == 201
    data = response.json()
    assert data["currency"] == "RUB"
    assert data["user_id"] == 999
    assert "id" in data


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Интеграционный тест требует RUN_INTEGRATION_TESTS=1 и запущенного PostgreSQL",
)
@pytest.mark.asyncio
async def test_create_wallet_real_db():
    """Интеграционный тест: выполняется против реальной БД при RUN_INTEGRATION_TESTS=1."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/wallets/?user_id=9999", json={"currency": "RUB"})

    assert response.status_code == 201
    data = response.json()
    assert data["currency"] == "RUB"
    assert data["user_id"] == 9999
    assert "id" in data
