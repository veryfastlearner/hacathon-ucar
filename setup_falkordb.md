# FalkorDB Setup Instructions

## Option 1: Docker (Recommended)
```bash
docker run -d --name falkordb -p 7687:7687 -p 7474:7474 falkordb/falkordb
```

## Option 2: Local Install
Download from https://www.falkordb.com/ and follow installation guide.

## Verify Connection
After setup, test with:
```python
import falkordb
graph_db = falkordb.GraphDatabase("bolt://localhost:7687", username="", password="")
print(graph_db)
```

## Run GraphRAG Bridge
Once FalkorDB is running, execute:
```bash
python graph_rag_bridge.py
```
