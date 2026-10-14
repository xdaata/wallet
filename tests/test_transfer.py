import pytest
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Wallet, TransactionType, TransactionStatus
from app.repositories.transaction import TransactionRepository
from app.repositories.wallet import WalletRepository
from app.services.wallet import WalletService


async def _make_wallets(session: AsyncSession, balances: list[str]) -> list[int]:
    # создаем пользователя и по кошельку на каждый баланс, возвращаем id кошельков
    user = User(email="owner@example.com", hashed_password="pwd")
    session.add(user)
    await session.flush()

    wallets = [Wallet(user_id=user.id, balance=Decimal(b)) for b in balances]
    session.add_all(wallets)
    await session.commit()
    return [w.id for w in wallets]


async def _balance(session: AsyncSession, wallet_id: int) -> Decimal:
    wallet = await WalletRepository(session).get_by_id(wallet_id)
    return wallet.balance


@pytest.mark.asyncio
async def test_transfer_success(db_session: AsyncSession):
    first, second = await _make_wallets(db_session, ["100.00", "0.00"])

    tx = await WalletService(db_session).transfer(first, second, Decimal("40.00"))

    assert tx.transaction_type == TransactionType.TRANSFER
    assert tx.status == TransactionStatus.COMPLETED
    assert tx.wallet_id == first
    assert await _balance(db_session, first) == Decimal("60.00")
    assert await _balance(db_session, second) == Decimal("40.00")


@pytest.mark.asyncio
async def test_transfer_to_higher_id(db_session: AsyncSession):
    # направление "меньший id -> больший id" и обратное должны работать одинаково
    first, second = await _make_wallets(db_session, ["0.00", "100.00"])

    await WalletService(db_session).transfer(second, first, Decimal("30.00"))

    assert await _balance(db_session, first) == Decimal("30.00")
    assert await _balance(db_session, second) == Decimal("70.00")


@pytest.mark.asyncio
@pytest.mark.parametrize("from_offset, to_offset", [(0, 999), (999, 0)])
async def test_transfer_missing_wallet_returns_404(
        db_session: AsyncSession, from_offset: int, to_offset: int
):
    (existing,) = await _make_wallets(db_session, ["100.00"])

    with pytest.raises(HTTPException) as exc:
        await WalletService(db_session).transfer(
            existing + from_offset, existing + to_offset, Decimal("10.00")
        )

    assert exc.value.status_code == 404
    assert await _balance(db_session, existing) == Decimal("100.00")
    assert await TransactionRepository(db_session).get_wallet_transactions(existing) == []


@pytest.mark.asyncio
async def test_transfer_to_same_wallet_rejected(db_session: AsyncSession):
    (wallet_id,) = await _make_wallets(db_session, ["100.00"])

    with pytest.raises(HTTPException) as exc:
        await WalletService(db_session).transfer(wallet_id, wallet_id, Decimal("10.00"))

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_transfer_non_positive_amount_rejected(db_session: AsyncSession):
    first, second = await _make_wallets(db_session, ["100.00", "0.00"])

    with pytest.raises(HTTPException) as exc:
        await WalletService(db_session).transfer(first, second, Decimal("0"))

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_transfer_insufficient_funds_keeps_failed_record(db_session: AsyncSession):
    first, second = await _make_wallets(db_session, ["10.00", "0.00"])

    with pytest.raises(HTTPException) as exc:
        await WalletService(db_session).transfer(first, second, Decimal("50.00"))

    assert exc.value.status_code == 400
    assert await _balance(db_session, first) == Decimal("10.00")
    assert await _balance(db_session, second) == Decimal("0.00")

    txs = await TransactionRepository(db_session).get_wallet_transactions(first)
    assert len(txs) == 1
    assert txs[0].transaction_type == TransactionType.TRANSFER
    assert txs[0].status == TransactionStatus.FAILED
