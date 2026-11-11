import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer
from app.rag.models import Document

model = SentenceTransformer('BAAI/bge-small-en-v1.5')

async def retrieve_context(query: str, db: AsyncSession, limit: int = 3) -> str:
    query_vector = await asyncio.to_thread(model.encode, query)
    query_vector = query_vector.tolist()
    
    # Added a distance threshold (0.6). If the match isn't good enough, it won't return it.
    stmt = (
        select(Document)
        .order_by(Document.embedding.cosine_distance(query_vector))
        .where(Document.embedding.cosine_distance(query_vector) < 0.6)
        .limit(limit)
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    if not docs:
        return "No relevant security documents found."
        
    context = "Here are the most relevant security vulnerabilities from the database:\n\n"
    for doc in docs:
        context += f"[{doc.title}]: {doc.chunk_text}\n\n"
    return context
