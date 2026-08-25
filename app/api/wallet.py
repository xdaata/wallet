from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.transaction import TransactionResponse
from app.schemas.wallet import WalletCreate, WalletResponse
from app.services.wallet import WalletService
from app.repositories.wallet import WalletRepository
from app.repositories.transaction import TransactionRepository

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
        user_id: int,
        wallet_in: WalletCreate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=user_id,
            email=f"user_{user_id}@example.com",
            hashed_password="fake_password"
        )
        db.add(user)
        await db.commit()

    repo = WalletRepository(db)
    wallet = await repo.create(user_id=user_id, wallet_in=wallet_in)
    await db.commit()
    await db.refresh(wallet)
    return wallet


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(wallet_id: int, db: AsyncSession = Depends(get_db)):
    repo = WalletRepository(db)
    wallet = await repo.get_by_id(wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Кошелек не найден"
        )
    return wallet


@router.post("/{wallet_id}/deposit", response_model=TransactionResponse)
async def deposit_funds(
        wallet_id: int,
        amount: Decimal,
        x_idempotency_key: str = Header(..., description="Уникальный ключ идемпотентности"),
        db: AsyncSession = Depends(get_db)
):
    service = WalletService(db)
    return await service.deposit(wallet_id=wallet_id, amount=amount)


@router.post("/{wallet_id}/withdraw", response_model=TransactionResponse)
async def withdraw_funds(
        wallet_id: int,
        amount: Decimal,
        db: AsyncSession = Depends(get_db)
):
    service = WalletService(db)
    return await service.withdraw(wallet_id=wallet_id, amount=amount)


@router.post("/transfer", response_model=TransactionResponse)
async def transfer_funds(
        from_wallet_id: int,
        to_wallet_id: int,
        amount: Decimal,
        db: AsyncSession = Depends(get_db)
):
    service = WalletService(db)
    return await service.transfer(
        from_wallet_id=from_wallet_id, to_wallet_id=to_wallet_id, amount=amount
    )


@router.get("/{wallet_id}/transactions", response_model=List[TransactionResponse])
async def get_wallet_transactions(
        wallet_id: int, db: AsyncSession = Depends(get_db)
):
    repo = TransactionRepository(db)
    return await repo.get_wallet_transactions(wallet_id=wallet_id)
