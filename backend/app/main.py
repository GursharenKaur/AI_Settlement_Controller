from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.core.api.routes.ingestion import router as ingestion_router
from app.core.api.routes.settlements import router as settlements_router
from app.core.api.routes.transactions import router as transactions_router
from app.core.api.routes.reconciliation import router as reconciliation_router
from app.core.api.routes import exceptions
from app.core.api.routes.controlled_actions import router as controlled_actions_router
from app.core.api.routes.operational_control import router as operational_control_router
from app.core.api.routes.operational_risk import router as operational_risk_router
from app.core.api.routes.intelligence import router as intelligence_router
import logging
from app.core.logging import configure_logging

import time

configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Settlement Controller",
    description="AI-powered settlement drift detection and financial control system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "HTTP request: %s %s -> %s (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response

@app.exception_handler(Exception)
async def internal_server_error_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled application error: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(transactions_router)
app.include_router(settlements_router)
app.include_router(ingestion_router)
app.include_router(reconciliation_router)
app.include_router(exceptions.router)
app.include_router(controlled_actions_router)
app.include_router(operational_control_router)
app.include_router(operational_risk_router)
app.include_router(intelligence_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ready"}