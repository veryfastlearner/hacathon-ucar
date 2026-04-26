from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import secrets

from database import SessionLocal, User, FinancialRequest, RoleEnum, RequestStatusEnum, hash_password, init_db

app = FastAPI(title="UCAR Financial Request API")

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    fullName: str
    email: str
    role: str

    class Config:
        orm_mode = True

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

class FinancialRequestResponse(BaseModel):
    id: int
    title: str
    description: str
    type: str
    amount: float
    currency: str
    department: str
    requestedBy: str
    status: str
    decisionBy: Optional[str] = None
    decisionNote: Optional[str] = None
    decisionDate: Optional[datetime] = None
    createdAt: datetime

    class Config:
        orm_mode = True

class DecisionPayload(BaseModel):
    decisionNote: Optional[str] = None
    userId: int # simplified auth token simulation

# Mock token storage for hackathon
active_tokens = {}

# Endpoints
@app.post("/auth/login", response_model=LoginResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Hash check
    if user.passwordHash != hash_password(login_req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = secrets.token_hex(16)
    active_tokens[token] = user.id
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "fullName": user.fullName,
            "email": user.email,
            "role": user.role.value
        }
    }

@app.get("/auth/me", response_model=UserResponse)
def get_me(token: str, db: Session = Depends(get_db)):
    user_id = active_tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "id": user.id,
        "fullName": user.fullName,
        "email": user.email,
        "role": user.role.value
    }

@app.get("/financial-requests", response_model=List[FinancialRequestResponse])
def get_requests(db: Session = Depends(get_db)):
    requests = db.query(FinancialRequest).order_by(FinancialRequest.createdAt.desc()).all()
    # ORM config covers mapping
    return requests

@app.get("/financial-requests/{req_id}", response_model=FinancialRequestResponse)
def get_request(req_id: int, db: Session = Depends(get_db)):
    req = db.query(FinancialRequest).filter(FinancialRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

def _get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

@app.post("/financial-requests/{req_id}/approve", response_model=FinancialRequestResponse)
def approve_request(req_id: int, payload: DecisionPayload, db: Session = Depends(get_db)):
    user = _get_user_by_id(db, payload.userId)
    if not user or user.role != RoleEnum.SECRETARY_GENERAL:
        raise HTTPException(status_code=403, detail="Only Secretary General can approve requests")
    
    req = db.query(FinancialRequest).filter(FinancialRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    req.status = RequestStatusEnum.APPROVED
    req.decisionBy = user.fullName
    req.decisionNote = payload.decisionNote
    req.decisionDate = datetime.utcnow()
    
    db.commit()
    db.refresh(req)
    return req

@app.post("/financial-requests/{req_id}/reject", response_model=FinancialRequestResponse)
def reject_request(req_id: int, payload: DecisionPayload, db: Session = Depends(get_db)):
    user = _get_user_by_id(db, payload.userId)
    if not user or user.role != RoleEnum.SECRETARY_GENERAL:
        raise HTTPException(status_code=403, detail="Only Secretary General can reject requests")
    
    req = db.query(FinancialRequest).filter(FinancialRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    req.status = RequestStatusEnum.REJECTED
    req.decisionBy = user.fullName
    req.decisionNote = payload.decisionNote
    req.decisionDate = datetime.utcnow()
    
    db.commit()
    db.refresh(req)
    return req

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
