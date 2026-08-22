from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    amount: Decimal
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    wallet_id: int


class TransactionResponse(TransactionBase):
    id: int
    wallet_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)