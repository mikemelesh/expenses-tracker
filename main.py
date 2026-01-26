from typing import List
from fastapi import FastAPI, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
import models, schemas
from database import get_db, Base, engine
import uvicorn


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expenses tracker")


@app.post("/expenses/", response_model=schemas.Expense, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
) -> models.ExpenseTable:
    db_expense = models.ExpenseTable(**expense.model_dump(), user_id=1)
    
    db.add(db_expense)
    db.commit()
    
    db.refresh(db_expense)
    return db_expense


@app.get("/expenses/", response_model=List[schemas.Expense])
def read_expenses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db)
) -> List[models.ExpenseTable]:
    """
    Retrieve a list of expenses with pagination.
    
    Args:
        skip: Offset for pagination.
        limit: Maximum number of items to return.
        db: Injected SQLAlchemy session.
        
    Returns:
        A list of Expense objects from the database.
    """
    # Use SQLAlchemy to query the table
    expenses = db.query(models.ExpenseTable).offset(skip).limit(limit).all()
    return expenses

    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
