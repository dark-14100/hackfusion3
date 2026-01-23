from fastapi import FastAPI
from api.chat import router as chat_router
from api.voice import router as voice_router

app = FastAPI(title="Pharmacy Agent - Feature 1")

app.include_router(chat_router)
app.include_router(voice_router)

# health check
@app.get("/health")
async def health():
    return {"status": "ok"}