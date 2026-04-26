#!/usr/bin/env python3
"""
Simple GraphRAG Bridge - Use working Gemini models
"""

import os
os.environ['SSLKEYLOGFILE'] = ''

import json, hashlib, numpy as np
from dotenv import load_dotenv
from supabase import create_client

# Use the working google-genai SDK (not deprecated google-generativeai)
from google import genai
from llama_index.core import StorageContext, PropertyGraphIndex, Document
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.graph_stores.falkordb import FalkorDBGraphStore
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import KGTableRetriever

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.getenv("gemini_api_key")

# Setup Gemini with working model
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
embed_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=GEMINI_API_KEY)

# Setup FalkorDB
graph_store = FalkorDBGraphStore(url="bolt://localhost:7687")
storage_context = StorageContext.from_defaults(graph_store=graph_store)

def fetch_chunks():
    """Fetch all text chunks from Supabase"""
    resp = supabase.table("ucar_documents").select("id, content, metadata").execute()
    return resp.data

def extract_entities_and_relationships(chunk_text, doc_id):
    """Use Gemini to extract entities and relationships from a chunk"""
    prompt = f"""
Extract entities and relationships from the following text chunk.
Return JSON with keys: "entities" (list of names) and "relationships" (list of [source, target, relation]).
Text: {chunk_text}
"""
    try:
        resp = gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        import re
        json_match = re.search(r'\{.*\}', resp.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group()), doc_id
    except Exception as e:
        print(f"[Gemini extraction error] {e}")
    return {"entities": [], "relationships": []}, doc_id

def build_semantic_bridge(chunks, threshold=0.85):
    """Create RELATED edges between chunks with high similarity"""
    print("Computing embeddings for semantic bridge...")
    embeddings = embed_model.get_text_embedding_batch([c["content"] for c in chunks])
    edges = []
    for i in range(len(chunks)):
        for j in range(i+1, len(chunks)):
            sim = np.dot(embeddings[i], embeddings[j]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
            )
            if sim > threshold:
                edges.append((chunks[i]["id"], chunks[j]["id"], "RELATED", {"similarity": float(sim)}))
    return edges

def build_graph_store():
    """Main pipeline to build and populate the graph store"""
    print("[1/5] Fetching chunks from Supabase...")
    chunks = fetch_chunks()
    print(f"Fetched {len(chunks)} chunks")

    print("[2/5] Extracting entities and relationships with Gemini...")
    all_entities = {}
    all_relationships = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        entities, rels = extract_entities_and_relationships(chunk["content"], chunk["id"])
        for e in entities["entities"]:
            all_entities[e] = {"type": "entity", "source": chunk["id"]}
        for rel in entities["relationships"]:
            all_relationships.append({
                "source": rel[0],
                "target": rel[1],
                "relation": rel[2],
                "properties": {"doc_id": chunk["id"]}
            })

    print("[3/5] Building semantic bridge with GeminiEmbedding...")
    semantic_edges = build_semantic_bridge(chunks, threshold=0.85)
    print(f"Created {len(semantic_edges)} semantic edges")

    print("[4/5] Creating documents...")
    docs = [Document(text=chunk["content"], doc_id=str(chunk["id"])) for chunk in chunks]

    print("[5/5] Building PropertyGraphIndex...")
    index = PropertyGraphIndex.from_documents(
        docs,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True
    )

    # Add extracted relationships to the graph
    for rel in all_relationships:
        try:
            index.upsert_triplet(rel["source"], rel["relation"], rel["target"], rel["properties"])
        except Exception as e:
            print(f"Failed to add relationship: {e}")

    # Add semantic bridge edges
    for src, tgt, rel, props in semantic_edges:
        try:
            index.upsert_triplet(f"doc_{src}", rel, f"doc_{tgt}", props)
        except Exception as e:
            print(f"Failed to add semantic edge: {e}")

    return index

def query_graph(index, question):
    """Query the graph using simple keyword search"""
    retriever = KGTableRetriever(index, include_text=True)
    query_engine = RetrieverQueryEngine.from_args(retriever)
    response = query_engine.query(question)
    return response

def main():
    print("🚀 Simple GraphRAG Bridge - Using modern google-genai SDK")
    try:
        kg_index = build_graph_store()
        print("\n✅ Graph built successfully!")
        
        print("\nYou can now ask questions about your UCAR data:")
        while True:
            q = input("\nAsk a question (or 'exit'): ")
            if q.lower() == 'exit':
                break
            answer = query_graph(kg_index, q)
            print("\nAnswer:", answer)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure FalkorDB is running: docker run -d --name falkordb -p 7687:7687 -p 7474:7474 falkordb/falkordb")

if __name__ == "__main__":
    main()
