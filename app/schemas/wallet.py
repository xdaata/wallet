from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class WalletBase(BaseModel):
    currency: str = "RUB"


class WalletCreate(WalletBase):
    pass


class WalletResponse(WalletBase):
    id: int
    user_id: int
    balance: Decimal
    model_config = ConfigDict(from_attributes=True)