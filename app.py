import os
from qdrant_client import QdrantClient, models
from groq import Groq
from dotenv import load_dotenv

# Load your GROQ_API_KEY from .env
load_dotenv()

# 1. Setup Clients
# Connect to the local folder you created during ingestion
client = QdrantClient(path="./qdrant_db")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

COLLECTION_NAME = "ucar_knowledge"

def ask_ucar(question):
    print(f"Searching local database for: {question}...")
    
    # 2. Vector Search
    # This automatically embeds the query and finds the best matches
    search_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=models.Document(text=question, model="Qdrant/fast-bge-small-en-v1.5"),
        limit=3
    ).points

    if not search_results:
        return "I couldn't find any relevant information in the uploaded documents."

    # 3. Context Preparation & Explainability
    context_chunks = []
    sources = set()
    
    for res in search_results:
        context_chunks.append(res.payload["document"])
        source_info = f"{res.payload['metadata']['source']} (Page {res.payload['metadata']['page']})"
        sources.add(source_info)

    context_text = "\n---\n".join(context_chunks)

    # 4. Groq Inference
    print("Consulting Llama 3...")
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": f"""You are the UCAR Institutional Intelligence Assistant. 
                Use the following context from official university documents to answer the user's question.
                Be precise, professional, and cite the findings.
                
                Context:
                {context_text}"""
            },
            {"role": "user", "content": question},
        ],
        model="llama-3.1-8b-instant",
        temperature=0.2, # Lower temperature = more factual
    )

    answer = chat_completion.choices[0].message.content
    source_list = "\n".join([f"- {s}" for s in sources])
    
    return f"{answer}\n\n📚 **Sources:**\n{source_list}"

if __name__ == "__main__":
    print("=== UCAR Smart Query Engine ===")
    while True:
        user_query = input("\nAsk a question (or type 'exit'): ")
        if user_query.lower() == 'exit':
            break
        
        try:
            result = ask_ucar(user_query)
            print(f"\n💡 RESPONSE:\n{result}")
        except Exception as e:
            print(f"❌ Error: {e}")