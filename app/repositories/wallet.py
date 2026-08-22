from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate


class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, wallet_in: WalletCreate) -> Wallet:
        wallet = Wallet(user_id=user_id, currency=wallet_in.currency)
        self.session.add(wallet)
        await self.session.commit()
        await self.session.refresh(wallet)
        return wallet

    async def get_by_id(self, wallet_id: int) -> Optional[Wallet]:
        result = await self.session.execute(select(Wallet).where(Wallet.id == wallet_id))
        return result.scalars().first()

    async def get_user_wallets(self, user_id: int) -> List[Wallet]:
        result = await self.session.execute(select(Wallet).where(Wallet.user_id == user_id))
        return list(result.scalars().all())