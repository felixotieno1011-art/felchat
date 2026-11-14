import asyncio
import re
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.models import Document

logger = logging.getLogger(__name__)
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        except Exception as e:
            logger.error(f"Embedding model failed to load: {e}")
            return None
    return _model

async def retrieve_context(query: str, db: AsyncSession, limit: int = 3) -> str:
    # FIX: If the user asks for an exact CVE ID, do a direct SQL lookup, not semantic search
    cve_match = re.search(r"(CVE-\d{4}-\d{4,7})", query, re.IGNORECASE)
    if cve_match:
        cve_id = cve_match.group(1).upper()
        stmt = select(Document).where(Document.title == cve_id)
        result = await db.execute(stmt)
        doc = result.scalars().first()
        if doc:
            return f"[{doc.title}]: {doc.chunk_text}"
        return f"No details found for {cve_id} in the database."

    # Skip RAG for very short messages (like "hi", "ok")
    if len(query.strip()) < 5:
        return ""

    model = get_model()
    if not model:
        return ""

    try:
        query_vector = await asyncio.to_thread(model.encode, query)
        query_vector = query_vector.tolist()
        
        # FIX: Add relevance cutoff. If distance > 0.6, it's not relevant.
        stmt = (
            select(Document)
            .order_by(Document.embedding.cosine_distance(query_vector))
            .where(Document.embedding.cosine_distance(query_vector) < 0.4)
            .limit(limit)
        )
        result = await db.execute(stmt)
        docs = result.scalars().all()
        
        if not docs:
            return ""
            
        context = "--- RELEVANT SECURITY KNOWLEDGE ---\n"
        for doc in docs:
            context += f"[{doc.title}]: {doc.chunk_text}\n\n"
        return context
    except Exception as e:
        logger.error(f"RAG Error: {e}")
        return ""
