# UCAR Data Pipeline Architecture

## Overview
This project scrapes data from UCAR (University of Carthage) and Times Higher Education, then builds knowledge graphs and AI-powered insights.

## System Architecture

```mermaid
graph TD
    %% Data Sources
    UCAR_WEB[UCAR Official Website] --> SCRAPE_PY
    THE_SITE[Times Higher Education] --> SCRAPE_THE
    
    %% Scrapers
    SCRAPE_PY[scrape.py<br/>BeautifulSoup scraper] --> UCAR_CSV
    SCRAPE_SPIDER[scrape_spider.py<br/>Scrapy spider] --> UCAR_CSV
    SCRAPE_THE[scrape_the.py<br/>THE rankings scraper] --> THE_CSV
    
    %% Raw Data Outputs
    UCAR_CSV[ucar_data_*.csv<br/>5 CSV files] --> UCAR_XLSX
    THE_CSV[the_ucar_rankings_*.csv<br/>8 CSV files] --> THE_XLSX
    
    UCAR_XLSX[ucar_data.xlsx]
    THE_XLSX[the_ucar_rankings.xlsx]
    
    %% Knowledge Graph Pipeline
    UCAR_CSV --> KG_BUILDER
    THE_CSV --> KG_BUILDER
    
    KG_BUILDER[knowledge_graph.py<br/>Graph builder + Plotly viz] --> KG_HTML
    KG_BUILDER --> KPI_HTML
    
    KG_HTML[knowledge_graph.html<br/>Interactive network graph]
    KPI_HTML[kpi_dashboard.html<br/>KPI visualizations]
    
    %% Semantic Analysis
    UCAR_CSV --> SEMANTIC_APP
    SUPABASE[(Supabase<br/>Vector embeddings)] --> SEMANTIC_APP
    
    SEMANTIC_APP[semantic_app.py<br/>UMAP + KMeans clustering] --> SEMANTIC_VIZ
    SEMANTIC_VIZ[university_carthage_graph.html<br/>Semantic knowledge graph]
    
    %% Insight Engine
    SUPABASE --> INSIGHT_ENGINE
    
    INSIGHT_ENGINE[insight_engine.py<br/>Fact extraction + Anomaly detection] --> INSIGHT_DASH
    INSIGHT_ENGINE --> GEMINI[Gemini API<br/>Synthesis + Recommendations]
    
    INSIGHT_DASH[insight_template.html<br/>AI-powered dashboard]
    
    %% Data Flow Summary
    subgraph DataSources[Data Sources]
        UCAR_WEB
        THE_SITE
    end
    
    subgraph Scrapers[Web Scrapers]
        SCRAPE_PY
        SCRAPE_SPIDER
        SCRAPE_THE
    end
    
    subgraph RawData[Raw Data]
        UCAR_CSV
        THE_CSV
        UCAR_XLSX
        THE_XLSX
    end
    
    subgraph KnowledgeGraph[Knowledge Graph Layer]
        KG_BUILDER
        KG_HTML
        KPI_HTML
    end
    
    subgraph SemanticLayer[Semantic Analysis Layer]
        SEMANTIC_APP
        SEMANTIC_VIZ
        SUPABASE
    end
    
    subgraph InsightLayer[AI Insight Layer]
        INSIGHT_ENGINE
        INSIGHT_DASH
        GEMINI
    end
```

## Core Components

### 1. Data Collection Layer
- **scrape.py**: BeautifulSoup-based scraper for UCAR website
- **scrape_spider.py**: Scrapy spider for crawling UCAR pages
- **scrape_the.py**: Scraper for Times Higher Education rankings

### 2. Data Storage Layer
- **CSV Files**: 13 total CSV files (5 UCAR + 8 THE rankings)
- **Excel Files**: Consolidated data in .xlsx format
- **Supabase**: Vector embeddings for semantic search

### 3. Knowledge Graph Layer
- **knowledge_graph.py**: Builds entity-relationship graphs from CSV data
- **knowledge_graph.html**: Interactive Plotly network visualization
- **kpi_dashboard.html**: Key performance indicators dashboard

### 4. Semantic Analysis Layer
- **semantic_app.py**: UMAP dimensionality reduction + KMeans clustering
- **university_carthage_graph.html**: Semantic knowledge graph visualization
- **Supabase**: Stores document embeddings for vector search

### 5. AI Insight Layer
- **insight_engine.py**: Fact extraction, anomaly detection, correlation analysis
- **insight_template.html**: Interactive dashboard with AI-generated insights
- **Gemini API**: Synthesizes recommendations and causal chain analysis

## Data Flow

1. **Scrapers** fetch data from UCAR website and THE rankings
2. **Raw data** is saved as CSV/Excel files
3. **Knowledge graph builder** connects entities and relationships
4. **Semantic app** creates vector embeddings and clusters documents
5. **Insight engine** extracts facts, detects anomalies, generates AI insights

## Files to Commit

### Core Application
- scrape.py, scrape_spider.py, scrape_the.py
- knowledge_graph.py, semantic_app.py, insight_engine.py
- insight_template.html

### Data Outputs
- the_ucar_rankings_*.csv (8 files)
- ucar_data_*.csv (5 files)
- *.xlsx files
- knowledge_graph.html, kpi_dashboard.html, university_carthage_graph.html

### Documentation
- README.md, ARCHITECTURE.md, architecture.mmd
- .gitignore (protects API keys)

## Viewing the Architecture

The architecture diagram is available in two formats:
- **architecture.mmd**: Mermaid source file
- **ARCHITECTURE.md**: Markdown with embedded mermaid diagram

View online at: https://mermaid.live/ (paste contents of architecture.mmd)
