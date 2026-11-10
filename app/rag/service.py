import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer
from app.rag.models import Document

# Load the model once at startup
model = SentenceTransformer('BAAI/bge-small-en-v1.5')

async def retrieve_context(query: str, db: AsyncSession, limit: int = 3) -> str:
    # FIX: Run the CPU-bound encoding in a separate thread so it doesn't freeze the server
    query_vector = await asyncio.to_thread(model.encode, query)
    query_vector = query_vector.tolist()
    
    stmt = (
        select(Document)
        .order_by(Document.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    if not docs:
        return "No relevant CVEs found in the database."
        
    context = "Here are the most relevant security vulnerabilities from the database:\n\n"
    for doc in docs:
        context += f"[{doc.title}]: {doc.chunk_text}\n\n"
    return context
