#!/usr/bin/env python3
"""
Standalone GraphRAG Bridge - Works without external graph database
Uses in-memory graph storage for demonstration
"""

import os
os.environ['SSLKEYLOGFILE'] = ''

import json, hashlib, numpy as np
from dotenv import load_dotenv
from supabase import create_client
from google import genai
from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core.query_engine import RetrieverQueryEngine

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.getenv("gemini_api_key")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Setup Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
embed_model = GeminiEmbedding(model_name="text-embedding-004", api_key=GEMINI_API_KEY)

# In-memory graph storage
class SimpleGraphStore:
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    def add_node(self, node_id, label, properties=None):
        self.nodes[node_id] = {"label": label, "properties": properties or {}}
    
    def add_edge(self, source, target, relation, properties=None):
        self.edges.append({
            "source": source,
            "target": target,
            "relation": relation,
            "properties": properties or {}
        })
    
    def get_related_nodes(self, node_id, relation=None):
        related = []
        for edge in self.edges:
            if edge["source"] == node_id or edge["target"] == node_id:
                if relation is None or edge["relation"] == relation:
                    related.append(edge)
        return related

graph = SimpleGraphStore()

def fetch_chunks():
    """Fetch all text chunks from Supabase"""
    resp = supabase.table("ucar_documents").select("id, content, metadata").execute()
    return resp.data

def extract_entities_and_relationships(chunk_text, doc_id):
    """Simple keyword extraction when Gemini is unavailable"""
    import re
    # Extract capitalized words as potential entities
    entities = list(set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', chunk_text)))
    # Simple relationship patterns
    relationships = []
    patterns = [
        (r'(\w+)\s+(is|was|are|were)\s+(\w+)', 'IS_A'),
        (r'(\w+)\s+(has|have|had)\s+(\w+)', 'HAS'),
        (r'(\w+)\s+(works?\s+for|works?\s+at)\s+(\w+)', 'WORKS_FOR'),
    ]
    for pattern, rel_type in patterns:
        matches = re.findall(pattern, chunk_text, re.IGNORECASE)
        for match in matches:
            relationships.append([match[0], rel_type, match[2]])
    
    return {"entities": entities[:10], "relationships": relationships[:5]}, doc_id

def build_semantic_bridge(chunks, threshold=0.3):
    """Create RELATED edges between chunks with high similarity using TF-IDF"""
    print("Computing TF-IDF similarity for semantic bridge...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    texts = [c["content"] for c in chunks]
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    similarities = cosine_similarity(tfidf_matrix)
    
    edges = []
    for i in range(len(chunks)):
        for j in range(i+1, len(chunks)):
            sim = similarities[i][j]
            if sim > threshold:
                edges.append((chunks[i]["id"], chunks[j]["id"], "RELATED", {"similarity": float(sim)}))
    return edges

def build_graph():
    """Build the in-memory graph"""
    print("[1/4] Fetching chunks from Supabase...")
    chunks = fetch_chunks()
    print(f"Fetched {len(chunks)} chunks")

    print("[2/4] Extracting entities and relationships with Gemini...")
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        entities, rels = extract_entities_and_relationships(chunk["content"], chunk["id"])
        
        # Add document node
        graph.add_node(f"doc_{chunk['id']}", f"Document {chunk['id']}", {"content": chunk["content"][:100]})
        
        # Add entity nodes
        for e in entities["entities"]:
            graph.add_node(e, e, {"type": "entity"})
            graph.add_edge(f"doc_{chunk['id']}", e, "MENTIONS")
        
        # Add relationship edges
        for rel in entities["relationships"]:
            if len(rel) >= 3:
                graph.add_edge(rel[0], rel[2], rel[1])

    print("[3/4] Building semantic bridge...")
    semantic_edges = build_semantic_bridge(chunks, threshold=0.3)
    for src, tgt, rel, props in semantic_edges:
        graph.add_edge(f"doc_{src}", f"doc_{tgt}", rel, props)
    print(f"Created {len(semantic_edges)} semantic edges")

    print("[4/4] Building TF-IDF index for search...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    texts = [chunk["content"] for chunk in chunks]
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    class SimpleIndex:
        def __init__(self, texts, vectorizer, matrix):
            self.texts = texts
            self.vectorizer = vectorizer
            self.matrix = matrix
        
        def retrieve(self, query, top_k=3):
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.matrix).flatten()
            top_indices = similarities.argsort()[-top_k:][::-1]
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    node = type('Node', (), {
                        'text': self.texts[idx],
                        'metadata': {'doc_id': str(idx)}
                    })()
                    results.append(type('NodeWithScore', (), {'node': node})(node))
            return results
    
    index = SimpleIndex(texts, vectorizer, tfidf_matrix)
    
    return index

def query_system(index, question):
    """Query both vector index and graph"""
    # Vector search
    nodes = index.retrieve(question, top_k=3)
    
    print("\n🔍 Vector Search Results:")
    for node in nodes:
        print(f"- {node.node.metadata.get('doc_id', 'Unknown')}: {node.node.text[:100]}...")
    
    # Simple graph traversal
    print("\n🕸️  Graph Context:")
    for node_id, node_data in graph.nodes.items():
        if question.lower() in node_data["label"].lower():
            related = graph.get_related_nodes(node_id)
            for edge in related[:3]:  # Limit to 3 related edges
                other = edge["target"] if edge["source"] == node_id else edge["source"]
                print(f"- {node_data['label']} --{edge['relation']}--> {graph.nodes.get(other, {}).get('label', other)}")
    
    # Generate simple answer from context
    context = "\n".join([node.node.text for node in nodes])
    if context:
        return f"Based on UCAR documents: {context[:300]}..."
    else:
        return "No relevant information found in the documents."

def main():
    print("🚀 Standalone GraphRAG Bridge - No external database required")
    
    try:
        index = build_graph()
        print(f"\n✅ Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        
        print("\nYou can now ask questions about your UCAR data:")
        while True:
            q = input("\nAsk a question (or 'exit'): ")
            if q.lower() == 'exit':
                break
            answer = query_system(index, q)
            print(f"\n💡 Answer: {answer}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
