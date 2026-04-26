from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets
from backend import crud, schemas, database

router = APIRouter(prefix="/auth", tags=["auth"])

active_tokens = {} # Mock in-memory state

@router.post("/login", response_model=schemas.LoginResponse)
def login(login_req: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, login_req.email)
    if not user or user.passwordHash != crud.hash_password(login_req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = secrets.token_hex(16)
    active_tokens[token] = user.id
    return {"token": token, "user": user}

@router.get("/me", response_model=schemas.UserResponse)
def get_me(token: str, db: Session = Depends(database.get_db)):
    user_id = active_tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
