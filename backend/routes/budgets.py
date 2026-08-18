import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.get("/current", response_model=Optional[schemas.BudgetResponse])
def get_current_budget(db: Session = Depends(get_db)):
    current_month = datetime.date.today().strftime("%Y-%m")
    budget = db.query(models.Budget).filter(models.Budget.month == current_month).first()
    return budget

@router.post("", response_model=schemas.BudgetResponse)
def create_budget(budget_in: schemas.BudgetCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Budget).filter(models.Budget.month == budget_in.month).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BUDGET ALREADY LOCKED FOR THIS CYCLE"
        )
    
    budget = models.Budget(
        month=budget_in.month,
        amount=budget_in.amount
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget
