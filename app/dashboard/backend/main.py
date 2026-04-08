from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from routers.countries import router as countries_router
from routers.qa import router as qa_router
from routers.research import router as research_router
from routers.analysis import router as analysis_router
from routers.opportunity import router as opportunity_router
from routers.admin import router as admin_router
from routers.insight import router as insight_router

logger = logging.getLogger("voc_dashboard.api")

app = FastAPI(title="VOC Data Product API", version="2.0.0")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)
    if isinstance(exc, RequestValidationError):
        return await request_validation_exception_handler(request, exc)
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


app.include_router(countries_router, prefix="/api/v1/countries", tags=["countries"])
app.include_router(research_router, prefix="/api/v1/research", tags=["research"])
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(opportunity_router, prefix="/api/v1/opportunity", tags=["opportunity"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(insight_router, prefix="/api/v1/insight", tags=["insight"])
app.include_router(qa_router, prefix="/api/v1/qa", tags=["qa"])
