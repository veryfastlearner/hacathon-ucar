#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

candidates = [
    "embeddings", "documents", "vectors", "items", "chunks",
    "nodes", "entities", "knowledge", "texts", "pages",
    "sites", "urls", "content", "vectors_store", "semantic"
]

for t in candidates:
    try:
        resp = client.table(t).select("*").limit(2).execute()
        if resp.data:
            print(f"\n=== TABLE: {t} ===")
            print(f"Rows sampled: {len(resp.data)}")
            print(f"Columns: {list(resp.data[0].keys())}")
            print(f"First row preview: {str(resp.data[0])[:400]}")
    except Exception as e:
        pass  # table doesn't exist or no access

# Also try to call a generic RPC if available to list tables
print("\n--- Trying RPC ---")
try:
    rpc_resp = client.rpc("get_tables", {}).execute()
    print("RPC get_tables:", rpc_resp.data)
except Exception as e:
    print("RPC failed:", e)
