#!/usr/bin/env python3
"""Fetch ucar_documents from Supabase to inspect."""
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

resp = client.table("ucar_documents").select("id, content, metadata").limit(5).execute()
print("Sample rows:")
for row in resp.data:
    print(f"\nID: {row['id']}")
    print(f"Content: {str(row['content'])[:300]}")
    print(f"Metadata: {row.get('metadata')}")

# Count total
resp2 = client.table("ucar_documents").select("id", count="exact").execute()
print(f"\nTotal rows: {resp2.count}")
