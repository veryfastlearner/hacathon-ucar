this is made by following a microservice architecture


in each branch we will find one service, but for full app its on ocr_new branch. you will notice that we already deployed our chatbot (we named query engine) thus easy integration via iframe in my teammates work.

in each branch you find a readme file explaining the architecture.



# UCAR Smart Query Engine

A multi-agent RAG (Retrieval-Augmented Generation) system designed for University Carthage (UCAR). It helps users navigate institutional documents and access key performance indicators (KPIs) through a collaborative agent architecture.

## Deployment Architecture

```mermaid
graph TD
    User([User]) --> WebApp[Frontend - Vercel]
    WebApp -->|API Request| Backend[Backend - Railway]
    
    subgraph agents ["Agent Orchestration (Railway)"]
        Backend --> GK[Gatekeeper Agent]
        GK -- "Relevant" --> LIB[Librarian Agent]
        GK -- "Relevant" --> RES[Researcher Agent]
        
        LIB --> CONS[Constructor Agent]
        RES --> CONS[Constructor Agent]
    end

    subgraph knowledge ["Knowledge Layer"]
        LIB --> Supabase[(Vector Store - Supabase)]
        RES --> Tavily[Web Search - Tavily]
    end

    CONS -->|JSON Response| WebApp
    WebApp -->|Display| User
```

## Agents Overview

- **Gatekeeper:** Evaluates question relevance to UCAR and its 32 institutions. Prevents off-topic queries.
- **Librarian:** Performs semantic search across institutional documents stored in Supabase using local embeddings.
- **Researcher:** Accesses real-time data from the web via Tavily API to complement archived documents.
- **Constructor:** Synthesizes outputs from all agents into a professional response with citations and error handling.

## Tech Stack

- **Frontend:** React (Vercel)
- **Backend:** Flask / Python (Railway)
- **Large Language Model:** Groq (Llama 3.1)
- **Vector Database:** Supabase (pgvector)
- **Search API:** Tavily
- **Embeddings:** FastEmbed
- **Data Source:** PDF / Supabase Cloud
