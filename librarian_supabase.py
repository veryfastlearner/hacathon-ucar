from clients import supabase, embed_model

def librarian_supabase(question: str) -> dict:
    """Queries the Supabase Vector Store using FastEmbed embeddings."""
    print("\n☁️ [LIBRARIAN SUPABASE] Searching remote cloud database...")
    try:
        # 1. Generate embedding for the question
        query_vector = list(embed_model.embed([question]))[0].tolist()

        # 2. RPC call to match_documents (Standard Supabase Vector Search)
        # Note: We assume the 'match_documents' function is defined in Postgres
        response = supabase.rpc("match_documents", {
            "query_embedding": query_vector,
            "match_threshold": 0.5,
            "match_count": 4
        }).execute()

        results = response.data

        if not results:
            return {"success": False, "content": "", "sources": [], "error": "No relevant documents found in Supabase."}

        chunks  = []
        sources = []
        for r in results:
            chunks.append(r.get("content", ""))
            meta = r.get("metadata", {})
            src  = f"{meta.get('source','Unknown')} — Page {meta.get('page','?')}"
            if src not in sources:
                sources.append(src)

        print(f"   ✅ Found {len(chunks)} relevant cloud passages.")
        return {"success": True, "content": "\n---\n".join(chunks), "sources": sources}

    except Exception as e:
        print(f"   ❌ Librarian Supabase error: {e}")
        return {"success": False, "content": "", "sources": [], "error": str(e)}
