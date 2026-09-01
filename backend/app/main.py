from fastapi import FastAPI

from app.core.api.routes.ingestion import router as ingestion_router
from app.core.api.routes.settlements import router as settlements_router
from app.core.api.routes.transactions import router as transactions_router


app = FastAPI(
    title="AI Settlement Controller",
    description="AI-powered settlement drift detection and financial control system",
    version="0.1.0",
)


app.include_router(transactions_router)
app.include_router(settlements_router)
app.include_router(ingestion_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}