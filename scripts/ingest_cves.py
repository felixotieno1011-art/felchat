import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import httpx
from sqlalchemy import delete
from sentence_transformers import SentenceTransformer
from app.core.db import SessionLocal
from app.rag.models import Document

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=500"

async def main():
    print("1. Fetching CVEs from NIST...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.get(NVD_URL)
        res.raise_for_status()
        data = res.json()
        vulns = data.get("vulnerabilities", [])
        print(f"   Found {len(vulns)} CVEs.")

    print("2. Loading local embedding model...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')

    print("3. Cleaning up old data...")
    async with SessionLocal() as db:
        await db.execute(delete(Document))
        await db.commit()

    print("4. Generating embeddings and saving...")
    async with SessionLocal() as db:
        for i, item in enumerate(vulns):
            cve = item["cve"]
            cve_id = cve["id"]
            
            # Get the English description
            desc = next((d["value"] for d in cve["descriptions"] if d["lang"] == "en"), "No description.")
            
            try:
                # Generate embedding locally (no API limits!)
                vector = model.encode(desc).tolist()
                
                doc = Document(
                    source="NVD",
                    title=cve_id,
                    chunk_text=desc,
                    embedding=vector
                )
                db.add(doc)
                
                # Commit every 50 to save progress
                if (i + 1) % 50 == 0:
                    await db.commit()
                    print(f"   Processed {i + 1}/{len(vulns)}")
            except Exception as e:
                print(f"   Skipping {cve_id}: {e}")
                
        await db.commit()
    print("✅ Ingestion complete! Your RAG brain is ready.")

if __name__ == "__main__":
    asyncio.run(main())
