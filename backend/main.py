import uvicorn
import os
from fastapi import FastAPI
from backend.database import engine, Base, SessionLocal
from backend.crud import seed_db_if_empty
from backend.routers import auth, financial, ocr, labs, institutions

app = FastAPI(title="UCAR Financial Request API — Multi-Institution")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_db_if_empty(db)
    finally:
        db.close()
    os.makedirs("uploads/pdfs", exist_ok=True)
    os.makedirs("uploads/json", exist_ok=True)

app.include_router(auth.router)
app.include_router(financial.router)
app.include_router(ocr.router)
app.include_router(labs.router)
app.include_router(institutions.router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
