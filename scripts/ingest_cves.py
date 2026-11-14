import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import httpx
import datetime
from sqlalchemy import delete
from sentence_transformers import SentenceTransformer
from app.core.db import SessionLocal
from app.rag.models import Document

async def main():
    print("1. Loading local embedding model...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')

    print("2. Cleaning up old CVEs (but preserving Portfolio data)...")
    async with SessionLocal() as db:
        await db.execute(delete(Document).where(Document.source == "NVD"))
        await db.commit()

    # Fetch CVEs from the last 90 days
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(days=90)
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

    print(f"3. Fetching recent CVEs from NIST ({start_date.date()} to {end_date.date()})...")
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={start_str}&pubEndDate={end_str}&resultsPerPage=500"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.get(url)
        if res.status_code != 200:
            print(f"   NVD API failed: {res.status_code}")
            return
        data = res.json()
        vulns = data.get("vulnerabilities", [])
        print(f"   Found {len(vulns)} recent CVEs.")

    print("4. Generating embeddings and saving...")
    async with SessionLocal() as db:
        for i, item in enumerate(vulns):
            cve = item["cve"]
            cve_id = cve["id"]
            desc = next((d["value"] for d in cve["descriptions"] if d["lang"] == "en"), "No description.")
            
            try:
                vector = model.encode(desc).tolist()
                doc = Document(source="NVD", title=cve_id, chunk_text=desc, embedding=vector)
                db.add(doc)
                
                if (i + 1) % 50 == 0:
                    await db.commit()
                    print(f"   Processed {i + 1}/{len(vulns)}")
            except Exception as e:
                print(f"   Skipping {cve_id}: {e}")
                
        await db.commit()
    print("✅ Recent CVEs ingested successfully!")

if __name__ == "__main__":
    asyncio.run(main())
