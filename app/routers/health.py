import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request, conn: sqlite3.Connection = Depends(get_db)):
    llm = request.app.state.llm.name
    try:
        conn.execute("SELECT 1").fetchone()
    except sqlite3.Error:
        return JSONResponse(
            status_code=503, content={"status": "degraded", "database": "error", "llm_provider": llm}
        )
    return {"status": "ok", "database": "ok", "llm_provider": llm}
