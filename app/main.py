from fastapi import FastAPI
from app.api.wallet import router as wallet_router

app = FastAPI(title="Wallet Service API")
app.include_router(wallet_router)