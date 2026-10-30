import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import httpx
from sqlalchemy import delete
from sentence_transformers import SentenceTransformer
from app.core.db import SessionLocal
from app.rag.models import Document

# Your GitHub Repositories
REPOS = [
    "felixotieno1011-art/zero-trust-gateway",
    "felixotieno1011-art/cloud-native-siem",
    "felixotieno1011-art/recon-platform",
    "felixotieno1011-art/honeypot-factory",
    "felixotieno1011-art/felchat"
]

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
                    readme_text = res.text
                    print(f"   Fetched {repo}")
                    
                    # Split into chunks of ~1000 chars for better embedding
                    chunks = [readme_text[i:i+1000] for i in range(0, len(readme_text), 1000)]
                    
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
                    print(f"   Could not fetch {repo} (Status: {res.status_code})")
            
            await db.commit()
    print("✅ Portfolio projects successfully ingested into RAG!")

if __name__ == "__main__":
    asyncio.run(main())
