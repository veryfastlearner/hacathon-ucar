from fastapi import FastAPI
from app.models.schemas import ExtractionResult

app = FastAPI(title="UCAR DataHub - Document-to-KPI Engine")

@app.get("/")
def read_root():
    return {"service": "UCAR DataHub Track 1", "status": "online"}

@app.post("/api/upload")
def upload_file():
    return {"message": "File upload placeholder"}

@app.post("/api/process/{document_id}")
def process_doc(document_id: str):
    return {"message": f"Processing {document_id}"}

@app.post("/api/process-all")
def process_all():
    return {"message": "Use run_process_all.py for the batch process for now."}

@app.get("/api/documents")
def get_docs():
    return {"docs": []}

@app.get("/api/dashboard-ready")
def get_dashboard_ready():
    return {"data": []}
