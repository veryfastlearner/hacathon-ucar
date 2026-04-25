from clients import qdrant
from config import COLLECTION_NAME

def librarian(question: str) -> dict:
    """Queries the in-memory Qdrant database using FastEmbed."""
    print("\n📚 [LIBRARIAN] Searching local document database...")
    try:
        # Use client.query() which matches the client.add() FastEmbed pipeline
        results = qdrant.query(
            collection_name=COLLECTION_NAME,
            query_text=question,
            limit=4
        )

        if not results:
            return {"success": False, "content": "", "sources": [], "error": "No relevant documents found."}

        chunks  = []
        sources = []
        for r in results:
            chunks.append(r.document)
            meta = r.metadata or {}
            src  = f"{meta.get('source','Unknown')} — Page {meta.get('page','?')}"
            if src not in sources:
                sources.append(src)

        print(f"   ✅ Found {len(chunks)} relevant passages from: {', '.join(set(s.split('—')[0].strip() for s in sources))}")
        return {"success": True, "content": "\n---\n".join(chunks), "sources": sources}

    except Exception as e:
        print(f"   ❌ Librarian error: {e}")
        return {"success": False, "content": "", "sources": [], "error": str(e)}
