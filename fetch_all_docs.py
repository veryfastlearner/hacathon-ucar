#!/usr/bin/env python3
"""Fetch all Supabase docs and save locally for analysis."""
import os, json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
resp = supabase.table("ucar_documents").select("id, content, metadata, embedding").execute()

docs = resp.data
with open(os.path.join(os.path.dirname(__file__), "all_docs.json"), "w", encoding="utf-8") as f:
    json.dump(docs, f, ensure_ascii=False, indent=2)

print(f"Saved {len(docs)} documents to all_docs.json")
for i, d in enumerate(docs[:5]):
    print(f"\n--- Doc {i} ---")
    print(f"Source: {d.get('metadata',{}).get('source')}, Page: {d.get('metadata',{}).get('page')}")
    print(f"Content: {str(d['content'])[:400]}...")
