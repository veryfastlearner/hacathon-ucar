from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend import crud, schemas, database
from backend.models import RoleEnum, RequestStatusEnum

router = APIRouter(prefix="/financial-requests", tags=["financial"])

@router.get("/", response_model=List[schemas.FinancialRequestResponse])
def read_requests(institution_id: int = None, db: Session = Depends(database.get_db)):
    return crud.get_financial_requests(db, institution_id=institution_id)

@router.get("/{req_id}", response_model=schemas.FinancialRequestResponse)
def read_request(req_id: int, db: Session = Depends(database.get_db)):
    req = crud.get_financial_request(db, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

@router.post("/{req_id}/approve", response_model=schemas.FinancialRequestResponse)
def approve(req_id: int, payload: schemas.DecisionPayload, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_id(db, payload.userId)
    if not user or user.role != RoleEnum.SECRETARY_GENERAL:
        raise HTTPException(status_code=403, detail="Only Secretary General can approve requests")
    
    req = crud.get_financial_request(db, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return crud.update_request_status(db, req, RequestStatusEnum.APPROVED, user, payload.decisionNote)

@router.post("/{req_id}/reject", response_model=schemas.FinancialRequestResponse)
def reject(req_id: int, payload: schemas.DecisionPayload, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_id(db, payload.userId)
    if not user or user.role != RoleEnum.SECRETARY_GENERAL:
        raise HTTPException(status_code=403, detail="Only Secretary General can reject requests")
    
    req = crud.get_financial_request(db, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return crud.update_request_status(db, req, RequestStatusEnum.REJECTED, user, payload.decisionNote)
