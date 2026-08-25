from fastapi import FastAPI
from app.api import wallet
from app.core.middleware import IdempotencyMiddleware

app = FastAPI(title="Wallet Service API", version="0.1.0")

app.add_middleware(IdempotencyMiddleware)
app.include_router(wallet.router)
