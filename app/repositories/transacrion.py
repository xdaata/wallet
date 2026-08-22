from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, transaction_in: TransactionCreate) -> Transaction:
        transaction = Transaction(
            wallet_id=transaction_in.wallet_id,
            amount=transaction_in.amount,
            transaction_type=transaction_in.transaction_type
        )
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        result = await self.session.execute(select(Transaction).where(Transaction.id == transaction_id))
        return result.scalars().first()

    async def get_wallet_transactions(self, wallet_id: int) -> List[Transaction]:
        result = await self.session.execute(select(Transaction).where(Transaction.wallet_id == wallet_id))
        return list(result.scalars().all())