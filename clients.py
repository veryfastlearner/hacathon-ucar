import os
import fitz  # PyMuPDF
from qdrant_client import QdrantClient
from groq import Groq
from tavily import TavilyClient
from config import GROQ_API_KEY, TAVILY_API_KEY, DATA_FOLDER, COLLECTION_NAME

# Initialize LLM and Search Clients
groq = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def _build_memory_db() -> QdrantClient:
    """Load PDFs into an in-memory Qdrant instance using FastEmbed."""
    print("⏳ [startup] Loading documents into memory with FastEmbed...")
    client = QdrantClient(":memory:")
    docs, metadata = [], []

    if not os.path.exists(DATA_FOLDER):
        print(f"   ⚠️  Data folder '{DATA_FOLDER}' not found — librarian will be empty.")
        return client

    for filename in os.listdir(DATA_FOLDER):
        if not filename.lower().endswith(".pdf"):
            continue
        path = os.path.join(DATA_FOLDER, filename)
        try:
            doc = fitz.open(path)
            for page_num, page in enumerate(doc):
                text = page.get_text().strip()
                if len(text) > 50:
                    docs.append(text)
                    metadata.append({
                        "source": filename,
                        "page": page_num + 1,
                        "institution": "ENICAR" if "eni" in filename.lower() else "UCAR"
                    })
            print(f"   📄 Loaded: {filename} ({len(doc)} pages)")
            doc.close()
        except Exception as e:
            print(f"   ⚠️  Could not load {filename}: {e}")

    if docs:
        # client.add() uses FastEmbed under the hood for embedding
        client.add(collection_name=COLLECTION_NAME, documents=docs, metadata=metadata)
        print(f"   ✅ {len(docs)} passages embedded in memory.")
    else:
        print("   ⚠️  No documents found to load.")

    return client

# Global in-memory Qdrant — no file lock, no conflicts
qdrant = _build_memory_db()
