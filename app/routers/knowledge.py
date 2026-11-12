import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Depends

from app import repositories as repo
from app.deps import get_db, require_admin
from app.errors import Conflict
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseOut

router = APIRouter(tags=["knowledge-bases"])


@router.get("/knowledge-bases", response_model=List[KnowledgeBaseOut])
def list_knowledge_bases(category: Optional[str] = None, conn: sqlite3.Connection = Depends(get_db)):
    return [dict(r) for r in repo.list_knowledge(conn, category)]


@router.post(
    "/knowledge-bases",
    response_model=KnowledgeBaseOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_knowledge_base(body: KnowledgeBaseCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Admin only (header X-Admin-Key): KB memengaruhi jawaban chatbot, jadi tidak boleh publik."""
    try:
        row = repo.insert_knowledge(conn, body.category, body.keyword_triggers, body.title, body.content)
    except sqlite3.IntegrityError:
        raise Conflict("Knowledge base dengan judul tersebut sudah ada.")
    return dict(row)
