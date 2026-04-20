from fastapi import FastAPI
from app.webhook import router as webhook_router

app = FastAPI(title="SocietyFlow API")

app.include_router(webhook_router)

@app.get("/")
def health_check():
    return {"status": "SocietyFlow is running"}
