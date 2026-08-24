from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class WalletBase(BaseModel):
    currency: str = Field(default="RUB", description="Валюта кошелька")


class WalletCreate(WalletBase):
    pass


class WalletResponse(WalletBase):
    id: int
    user_id: int
    balance: Decimal = Field(
        description="Баланс кошелька",
        max_digits=12,
        decimal_places=2
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "currency": "RUB",
                "balance": "0.00"
            }
        }
    )