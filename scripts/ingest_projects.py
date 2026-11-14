import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import httpx
from sqlalchemy import delete
from sentence_transformers import SentenceTransformer
from app.core.db import SessionLocal
from app.rag.models import Document

REPOS = [
    "felixotieno1011-art/zero-trust-gateway",
    "felixotieno1011-art/cloud-native-siem",
    "felixotieno1011-art/recon-platform",
    "felixotieno1011-art/honeypot-factory",
    "felixotieno1011-art/felchat"
]

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """Splits text into overlapping chunks so we don't cut mid-sentence."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

async def main():
    print("1. Loading local embedding model...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')

    print("2. Cleaning up old project data...")
    async with SessionLocal() as db:
        await db.execute(delete(Document).where(Document.source == "Portfolio"))
        await db.commit()

    print("3. Fetching Project READMEs from GitHub...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with SessionLocal() as db:
            for repo in REPOS:
                url = f"https://raw.githubusercontent.com/{repo}/main/README.md"
                res = await client.get(url)
                
                if res.status_code == 200:
                    print(f"   Fetched {repo}")
                    chunks = chunk_text(res.text)
                    
                    for chunk in chunks:
                        vector = model.encode(chunk).tolist()
                        doc = Document(
                            source="Portfolio",
                            title=repo.split('/')[-1],
                            chunk_text=chunk,
                            embedding=vector
                        )
                        db.add(doc)
                else:
                    print(f"   Could not fetch {repo}")
            
            await db.commit()
    print("✅ Portfolio projects successfully ingested with overlap!")

if __name__ == "__main__":
    asyncio.run(main())
