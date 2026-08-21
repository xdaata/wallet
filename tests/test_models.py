import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Wallet, Transaction, TransactionType, TransactionStatus


@pytest.mark.asyncio
async def test_create_user_wallet_transaction(db_session: AsyncSession):
    # проверка корректности создания связанных сущностей и дефолтных значений
    user = User(email="test@example.com", hashed_password="hashed_pwd")
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None

    wallet = Wallet(user_id=user.id, currency="RUB")
    db_session.add(wallet)
    await db_session.flush()
    assert wallet.balance == Decimal("0.00")

    tx = Transaction(
        wallet_id=wallet.id,
        amount=Decimal("150.75"),
        transaction_type=TransactionType.DEPOSIT,
    )
    db_session.add(tx)
    await db_session.commit()
    assert tx.id is not None
    assert tx.status == TransactionStatus.PENDING
    assert tx.amount == Decimal("150.75")


@pytest.mark.asyncio
async def test_unique_email(db_session: AsyncSession):
    # проверка блокировки создания пользователей с одинаковой почтой
    user1 = User(email="unique@example.com", hashed_password="pwd")
    user2 = User(email="unique@example.com", hashed_password="pwd")

    db_session.add(user1)
    await db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_delete_wallet_after_user(db_session: AsyncSession):
    # проверка автоматического удаления кошелька при удалении владельца
    user = User(email="cascade@example.com", hashed_password="pwd")
    db_session.add(user)
    await db_session.flush()

    wallet = Wallet(user_id=user.id)
    db_session.add(wallet)
    await db_session.commit()
    await db_session.delete(user)
    await db_session.commit()
    deleted_wallet = await db_session.get(Wallet, wallet.id)
    assert deleted_wallet is None