#!/usr/bin/env python3
"""
Minimal GraphRAG Bridge - Manual Installation Required
"""

import os, json, hashlib
from dotenv import load_dotenv
from supabase import create_client
import numpy as np

from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Document
from llama_index.core.indices.knowledge_graph import KGIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import KGTableRetriever
from llama_index.core.storage.graph_store import SimpleGraphStore
import falkordb


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.getenv("gemini_api_key")

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
llm = Gemini(api_key=GEMINI_API_KEY, model="models/gemini-1.5-flash")
embed_model = GeminiEmbedding(api_key=GEMINI_API_KEY, model_name="models/embedding-001")

# FalkorDB connection (will fail if not running)
try:
    graph_db = falkordb.GraphDatabase("bolt://localhost:7687", username="", password="")
    graph_store = SimpleGraphStore(graph=graph_db)
    print("✓ Connected to FalkorDB")
except Exception as e:
    print(f"✗ FalkorDB connection failed: {e}")
    print("Please start FalkorDB with: docker run -d --name falkordb -p 7687:7687 -p 7474:7474 falkordb/falkordb")
    exit(1)

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
        response = llm.complete(prompt)
        import re
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
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

    print("[4/5] Populating FalkorDB graph store...")
    # Add entity nodes
    for entity, props in all_entities.items():
        graph_store.upsert_triplet(entity, "type", props["type"], props)

    # Add extracted relationships
    for rel in all_relationships:
        graph_store.upsert_triplet(rel["source"], rel["relation"], rel["target"], rel["properties"])

    # Add semantic bridge edges
    for src, tgt, rel, props in semantic_edges:
        graph_store.upsert_triplet(f"doc_{src}", rel, f"doc_{tgt}", props)

    print("[5/5] Creating KGIndex...")
    docs = [Document(text=chunk["content"], doc_id=str(chunk["id"])) for chunk in chunks]
    index = KGIndex.from_documents(docs, llm=llm, embed_model=embed_model, graph_store=graph_store)

    return index

def query_graph(index, question):
    """Query the graph using RetrieverQueryEngine"""
    retriever = KGTableRetriever(index, include_text=True)
    query_engine = RetrieverQueryEngine.from_args(retriever, llm=llm)
    response = query_engine.query(question)
    return response

if __name__ == "__main__":
    print("Building GraphRAG bridge...")
    kg_index = build_graph_store()
    
    print("\nGraph built! You can now ask questions.")
    while True:
        q = input("\nAsk a question (or 'exit'): ")
        if q.lower() == 'exit':
            break
        answer = query_graph(kg_index, q)
        print("\nAnswer:", answer)
