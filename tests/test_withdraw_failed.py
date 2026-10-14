import pytest
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Wallet, TransactionType, TransactionStatus
from app.repositories.transaction import TransactionRepository
from app.repositories.wallet import WalletRepository
from app.services.wallet import WalletService


async def _make_wallet(session: AsyncSession, balance: str) -> int:
    user = User(email="owner@example.com", hashed_password="pwd")
    session.add(user)
    await session.flush()

    wallet = Wallet(user_id=user.id, balance=Decimal(balance))
    session.add(wallet)
    await session.commit()
    return wallet.id


@pytest.mark.asyncio
async def test_withdraw_success(db_session: AsyncSession):
    wallet_id = await _make_wallet(db_session, "100.00")

    tx = await WalletService(db_session).withdraw(wallet_id, Decimal("30.00"))

    assert tx.status == TransactionStatus.COMPLETED
    assert tx.transaction_type == TransactionType.WITHDRAW
    wallet = await WalletRepository(db_session).get_by_id(wallet_id)
    assert wallet.balance == Decimal("70.00")


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds_keeps_failed_record(db_session: AsyncSession):
    wallet_id = await _make_wallet(db_session, "10.00")

    with pytest.raises(HTTPException) as exc:
        await WalletService(db_session).withdraw(wallet_id, Decimal("50.00"))

    assert exc.value.status_code == 400
    wallet = await WalletRepository(db_session).get_by_id(wallet_id)
    assert wallet.balance == Decimal("10.00")

    txs = await TransactionRepository(db_session).get_wallet_transactions(wallet_id)
    assert len(txs) == 1
    assert txs[0].transaction_type == TransactionType.WITHDRAW
    assert txs[0].status == TransactionStatus.FAILED


@pytest.mark.asyncio
async def test_withdraw_missing_wallet_returns_404(db_session: AsyncSession):
    with pytest.raises(HTTPException) as exc:
        await WalletService(db_session).withdraw(12345, Decimal("10.00"))

    assert exc.value.status_code == 404
