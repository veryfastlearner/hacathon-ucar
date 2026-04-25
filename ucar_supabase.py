import os
import fitz 
from supabase import create_client
from fastembed import TextEmbedding
from dotenv import load_dotenv

load_dotenv()

# API Keys from your Supabase Project Settings > API
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") 
supabase = create_client(url, key)
model = TextEmbedding()

def ingest_to_supabase(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            print(f"Uploading: {filename}")
            doc = fitz.open(os.path.join(folder_path, filename))
            
            for page in doc:
                text = page.get_text().strip()
                if len(text) < 100: continue # Skip tiny fragments

                # Create the vector locally (Free)
                vector = list(model.embed([text]))[0].tolist()

                # Insert into the database
                supabase.table("ucar_documents").insert({
                    "content": text,
                    "embedding": vector,
                    "metadata": {
                        "source": filename,
                        "page": page.number + 1,
                        "institution": "ENICarthage" if "eni" in filename.lower() else "UCAR"
                    }
                }).execute()
    print("✅ Supabase Knowledge Base is ready!")

ingest_to_supabase("./data")