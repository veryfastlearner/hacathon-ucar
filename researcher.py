from clients import tavily

def researcher(question: str) -> dict:
    """Searches the web via Tavily for up-to-date information."""
    print("\n🔍 [RESEARCHER] Searching the web for updated information...")
    try:
        search_query = f"University Carthage Tunisia UCAR {question}"
        result = tavily.search(
            query=search_query,
            search_depth="basic",
            max_results=3,
            include_answer=True
        )

        web_answer = result.get("answer", "")
        web_results = result.get("results", [])

        if not web_results and not web_answer:
            return {"success": False, "content": "", "sources": [], "error": "No web results found."}

        content_parts = []
        sources = []
        if web_answer:
            content_parts.append(f"Web Summary: {web_answer}")
        for r in web_results:
            content_parts.append(f"• {r.get('title','')}: {r.get('content','')[:400]}")
            sources.append(r.get("url", ""))

        print(f"   ✅ Found {len(web_results)} web results.")
        return {"success": True, "content": "\n\n".join(content_parts), "sources": sources}

    except Exception as e:
        print(f"   ❌ Researcher error: {e}")
        return {"success": False, "content": "", "sources": [], "error": str(e)}
