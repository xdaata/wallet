from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api import wallet
from app.core.middleware import IdempotencyMiddleware

app = FastAPI(title="Wallet Service API", version="0.1.0")
app.add_middleware(IdempotencyMiddleware)
app.include_router(wallet.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("static/index.html")
