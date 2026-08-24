import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_wallet_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/wallets/?user_id=999", json={"currency": "RUB"})

    assert response.status_code == 201
    data = response.json()
    assert data["currency"] == "RUB"
    assert data["user_id"] == 999
    assert "id" in data
