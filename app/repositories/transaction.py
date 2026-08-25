from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from decimal import Decimal

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self,
            wallet_id: int,
            amount: Decimal,
            transaction_type: TransactionType,
            status: TransactionStatus = TransactionStatus.PENDING,
    ) -> Transaction:
        transaction = Transaction(
            wallet_id=wallet_id,
            amount=amount,
            transaction_type=transaction_type,
            status=status,
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        result = await self.session.execute(select(Transaction).where(Transaction.id == transaction_id))
        return result.scalars().first()

    async def get_wallet_transactions(self, wallet_id: int) -> List[Transaction]:
        result = await self.session.execute(select(Transaction).where(Transaction.wallet_id == wallet_id))
        return list(result.scalars().all())
