from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.qa_runner import WorkbookQaRunner


router = APIRouter()
_PRODUCT_ROOT = Path(__file__).resolve().parents[4]
qa_runner = WorkbookQaRunner(_PRODUCT_ROOT)


class QaRequest(BaseModel):
    max_cells: int = Field(default=20000, ge=100, le=500000)


@router.post("/workbook-html-scan")
def workbook_html_scan(payload: QaRequest) -> dict:
    return qa_runner.scan_html_pollution(max_cells=payload.max_cells)

