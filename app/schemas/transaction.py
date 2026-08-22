from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.transaction import TransactionType, TransactionStatus


class TransactionBase(BaseModel):
    amount: Decimal
    transaction_type: TransactionType


class TransactionCreate(TransactionBase):
    wallet_id: int


class TransactionResponse(TransactionBase):
    id: int
    wallet_id: int
    status: TransactionStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)