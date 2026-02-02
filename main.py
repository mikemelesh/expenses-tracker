from typing import List, Dict
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import uvicorn
import models
import schemas
from database import get_db, Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expenses Tracker Pro")


@app.post("/expenses/", response_model=schemas.Expense, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: schemas.ExpenseCreate, 
    db: Session = Depends(get_db)
) -> models.ExpenseTable:
    """Creates an expense after validating the category exists."""
    category = db.query(models.CategoryTable).filter(models.CategoryTable.id == expense.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db_expense = models.ExpenseTable(**expense.model_dump(), user_id=1) 
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/expenses/", response_model=List[schemas.Expense])
def read_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db)
) -> List[models.ExpenseTable]:
    """Lists all expenses."""
    return db.query(models.ExpenseTable).offset(skip).limit(limit).all()

@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Deletes a specific expense."""
    db_expense = db.query(models.ExpenseTable).filter(models.ExpenseTable.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()
    return None


@app.post("/categories/", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """Creates a new category."""
    existing = db.query(models.CategoryTable).filter(models.CategoryTable.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    db_category = models.CategoryTable(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories/", response_model=List[schemas.Category])
def list_categories(db: Session = Depends(get_db)):
    """Lists all categories."""
    return db.query(models.CategoryTable).all()

@app.delete("/categories/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    """Deletes a category."""
    db_cat = db.query(models.CategoryTable).filter(models.CategoryTable.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_cat)
    db.commit()
    return None


@app.get("/stats/pie-chart")
def get_pie_chart_data(db: Session = Depends(get_db)) -> Dict[str, float]:
    """Aggregates expenses by category for the frontend chart."""
    stats = (
        db.query(
            models.CategoryTable.name, 
            func.sum(models.ExpenseTable.amount).label("total")
        )
        .join(models.ExpenseTable)
        .group_by(models.CategoryTable.name)
        .all()
    )
    return {name: total for name, total in stats}


@app.get("/", response_class=HTMLResponse)
async def main_page():
    """Renders the main dashboard with CRUD forms and Chart.js."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Expense Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: sans-serif; margin: 40px; display: flex; gap: 40px; }
            .container { flex: 1; }
            .chart-box { width: 400px; }
            form { margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
            input, select { margin-bottom: 10px; display: block; width: 100%; padding: 8px; }
            button { background: #28a745; color: white; border: none; padding: 10px; cursor: pointer; width: 100%; }
            .item { background: #f9f9f9; padding: 10px; margin-bottom: 5px; border-radius: 4px; display: flex; justify-content: space-between; }
            .del-btn { background: #dc3545; width: auto; padding: 5px 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Manage Categories</h2>
            <form id="catForm">
                <input id="catName" placeholder="Category Name (e.g. Food)" required>
                <input id="catIcon" placeholder="Icon (e.g. 🍕)">
                <button type="submit">Add Category</button>
            </form>
            <div id="catList"></div>

            <h2>Add Expense</h2>
            <form id="expForm">
                <input id="expAmt" type="number" step="0.01" placeholder="Amount" required>
                <input id="expDesc" placeholder="Description" required>
                <select id="expCat"></select>
                <button type="submit">Add Expense</button>
            </form>
            <div id="expList"></div>
        </div>

        <div class="chart-box">
            <h2>Spend Distribution</h2>
            <canvas id="myChart"></canvas>
        </div>

        <script>
            let chart;

            async function refreshAll() {
                const cats = await (await fetch('/categories/')).json();
                const exps = await (await fetch('/expenses/')).json();
                const stats = await (await fetch('/stats/pie-chart')).json();

                // Update Category Dropdown and List
                document.getElementById('catList').innerHTML = cats.map(c => 
                    `<div class="item">${c.icon} ${c.name} <button class="del-btn" onclick="deleteItem('categories', ${c.id})">X</button></div>`
                ).join('');
                
                document.getElementById('expCat').innerHTML = cats.map(c => 
                    `<option value="${c.id}">${c.name}</option>`
                ).join('');

                // Update Expense List
                document.getElementById('expList').innerHTML = exps.map(e => 
                    `<div class="item">$${e.amount} - ${e.description} <button class="del-btn" onclick="deleteItem('expenses', ${e.id})">X</button></div>`
                ).join('');

                // Update Chart
                const ctx = document.getElementById('myChart').getContext('2d');
                if (chart) chart.destroy();
                chart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(stats),
                        datasets: [{ data: Object.values(stats), backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'] }]
                    }
                });
            }

            async function deleteItem(type, id) {
                await fetch(`/${type}/${id}`, { method: 'DELETE' });
                refreshAll();
            }

            document.getElementById('catForm').onsubmit = async (e) => {
                e.preventDefault();
                const name = document.getElementById('catName').value;
                const icon = document.getElementById('catIcon').value;
                await fetch('/categories/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name, icon })
                });
                refreshAll();
            };

            document.getElementById('expForm').onsubmit = async (e) => {
                e.preventDefault();
                const amount = document.getElementById('expAmt').value;
                const description = document.getElementById('expDesc').value;
                const category_id = document.getElementById('expCat').value;
                await fetch('/expenses/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ amount, description, category_id })
                });
                refreshAll();
            };

            refreshAll();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)