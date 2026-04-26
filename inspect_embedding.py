#!/usr/bin/env python3
import os, json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
resp = client.table("ucar_documents").select("embedding").limit(1).execute()
emb = resp.data[0]["embedding"]
print("Type:", type(emb))
print("Dim:", len(emb) if isinstance(emb, list) else "N/A")
print("First 5:", str(emb)[:200])
