#!/usr/bin/env python3
"""Quick Supabase schema & data explorer."""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

# List public tables
resp = client.table("information_schema.tables").select("table_name").eq("table_schema", "public").execute()
print("Public tables:", [r["table_name"] for r in resp.data])

# For each table, print a sample row
for r in resp.data:
    t = r["table_name"]
    try:
        sample = client.table(t).select("*").limit(1).execute()
        if sample.data:
            cols = list(sample.data[0].keys())
            print(f"\n{t}: cols={cols}, sample keys only")
    except Exception as e:
        print(f"\n{t}: error sampling -> {e}")
