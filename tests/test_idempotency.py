import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient


async def _create_wallet(client: AsyncClient) -> int:
    response = await client.post("/wallets/?user_id=1", json={"currency": "RUB"})
    assert response.status_code == 201
    return response.json()["id"]


async def _balance(client: AsyncClient, wallet_id: int) -> Decimal:
    response = await client.get(f"/wallets/{wallet_id}")
    return Decimal(response.json()["balance"])


@pytest.mark.asyncio
async def test_same_key_same_params_executes_once(client: AsyncClient):
    wallet_id = await _create_wallet(client)
    headers = {"x-idempotency-key": str(uuid.uuid4())}
    url = f"/wallets/{wallet_id}/deposit?amount=500.00"

    first = await client.post(url, headers=headers)
    second = await client.post(url, headers=headers)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert await _balance(client, wallet_id) == Decimal("500.00")

    history = await client.get(f"/wallets/{wallet_id}/transactions")
    assert len(history.json()) == 1


@pytest.mark.asyncio
async def test_same_key_different_amount_is_new_request(client: AsyncClient):
    wallet_id = await _create_wallet(client)
    headers = {"x-idempotency-key": str(uuid.uuid4())}

    await client.post(f"/wallets/{wallet_id}/deposit?amount=500.00", headers=headers)
    await client.post(f"/wallets/{wallet_id}/deposit?amount=100.00", headers=headers)

    assert await _balance(client, wallet_id) == Decimal("600.00")


@pytest.mark.asyncio
async def test_error_responses_are_not_cached(client: AsyncClient):
    wallet_id = await _create_wallet(client)
    headers = {"x-idempotency-key": str(uuid.uuid4())}
    withdraw_url = f"/wallets/{wallet_id}/withdraw?amount=50.00"

    failed = await client.post(withdraw_url, headers=headers)
    assert failed.status_code == 400

    await client.post(
        f"/wallets/{wallet_id}/deposit?amount=100.00",
        headers={"x-idempotency-key": str(uuid.uuid4())},
    )
    retried = await client.post(withdraw_url, headers=headers)

    assert retried.status_code == 200
    assert await _balance(client, wallet_id) == Decimal("50.00")


@pytest.mark.asyncio
async def test_mutating_endpoints_require_idempotency_key(client: AsyncClient):
    wallet_id = await _create_wallet(client)
    # deposit without header -> 422
    res_dep = await client.post(f"/wallets/{wallet_id}/deposit?amount=50.00")
    assert res_dep.status_code == 422

    # withdraw without header -> 422
    res_w = await client.post(f"/wallets/{wallet_id}/withdraw?amount=50.00")
    assert res_w.status_code == 422

    # transfer without header -> 422
    res_tr = await client.post(f"/wallets/transfer?from_wallet_id={wallet_id}&to_wallet_id={wallet_id}&amount=50.00")
    assert res_tr.status_code == 422


@pytest.mark.asyncio
async def test_transfer_idempotency(client: AsyncClient):
    w1 = await _create_wallet(client)
    w2 = await _create_wallet(client)

    await client.post(
        f"/wallets/{w1}/deposit?amount=100.00",
        headers={"x-idempotency-key": str(uuid.uuid4())}
    )

    transfer_headers = {"x-idempotency-key": str(uuid.uuid4())}
    url = f"/wallets/transfer?from_wallet_id={w1}&to_wallet_id={w2}&amount=40.00"

    first = await client.post(url, headers=transfer_headers)
    second = await client.post(url, headers=transfer_headers)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert await _balance(client, w1) == Decimal("60.00")
    assert await _balance(client, w2) == Decimal("40.00")