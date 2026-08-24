from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.repositories.wallet import WalletRepository
from app.repositories.transaction import TransactionRepository


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallet_repo = WalletRepository(session)
        self.tx_repo = TransactionRepository(session)

    async def deposit(self, wallet_id: int, amount: Decimal) -> Transaction:
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сумма пополнения должна быть больше 0"
            )

        async with self.session.begin():
            wallet = await self.wallet_repo.get_by_id(wallet_id, lock=True)
            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Кошелек не найден"
                )

            wallet.balance += amount

            tx = await self.tx_repo.create(
                wallet_id=wallet.id,
                amount=amount,
                transaction_type=TransactionType.DEPOSIT,
                status=TransactionStatus.COMPLETED
            )

        return tx

    async def withdraw(self, wallet_id: int, amount: Decimal) -> Transaction:
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сумма списания должна быть больше 0"
            )

        async with self.session.begin():
            wallet = await self.wallet_repo.get_by_id(wallet_id, lock=True)
            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Кошелек не найден"
                )

            if wallet.balance < amount:
                await self.tx_repo.create(
                    wallet_id=wallet.id,
                    amount=amount,
                    transaction_type=TransactionType.WITHDRAW,
                    status=TransactionStatus.FAILED
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Недостаточно средств на балансе"
                )

            wallet.balance -= amount

            tx = await self.tx_repo.create(
                wallet_id=wallet.id,
                amount=amount,
                transaction_type=TransactionType.WITHDRAW,
                status=TransactionStatus.COMPLETED
            )

        return tx

    async def transfer(self, from_wallet_id: int, to_wallet_id: int, amount: Decimal) -> Transaction:
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сумма перевода должна быть больше 0"
            )

        if from_wallet_id == to_wallet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя перевести деньги на тот же самый кошелек"
            )

        async with self.session.begin():
            first_id, second_id = sorted([from_wallet_id, to_wallet_id])

            first_wallet = await self.wallet_repo.get_by_id(first_id, lock=True)
            second_wallet = await self.wallet_repo.get_by_id(second_id, lock=True)

            sender = first_wallet if first_wallet and first_wallet.id == from_wallet_id else second_wallet
            receiver = second_wallet if second_wallet and second_wallet.id == to_wallet_id else first_wallet

            if not sender or not receiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Один из кошельков не найден"
                )

            if sender.balance < amount:
                await self.tx_repo.create(
                    wallet_id=sender.id,
                    amount=amount,
                    transaction_type=TransactionType.TRANSFER,
                    status=TransactionStatus.FAILED
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Недостаточно средств для перевода"
                )

            sender.balance -= amount
            receiver.balance += amount

            tx = await self.tx_repo.create(
                wallet_id=sender.id,
                amount=amount,
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED
            )

        return tx