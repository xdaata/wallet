from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate


class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, wallet_in: WalletCreate) -> Wallet:
        wallet = Wallet(user_id=user_id, currency=wallet_in.currency)
        self.session.add(wallet)
        await self.session.flush()
        return wallet

    async def get_by_id(self, wallet_id: int, lock: bool = False) -> Optional[Wallet]:
        query = select(Wallet).where(Wallet.id == wallet_id)
        if lock:
            query = query.with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_wallets(self, user_id: int) -> List[Wallet]:
        result = await self.session.execute(select(Wallet).where(Wallet.user_id == user_id))
        return list(result.scalars().all())
