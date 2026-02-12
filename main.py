#python -m uvicorn main:app --reload

from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import sqlite3

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")  # For HTML interface

# -----------------------
# Root route for health check
# -----------------------
@app.get("/")
def root():
    return {"message": "SentinelStream API is running"}

# -----------------------
# HTML interface route
# -----------------------
@app.get("/submit-transaction", response_class=HTMLResponse)
def home(request: Request):
    """
    HTML form for users to submit transactions
    """
    return templates.TemplateResponse("index.html", {"request": request})

# -----------------------
# Handle form submission
# -----------------------
@app.post("/submit-transaction", response_class=HTMLResponse)
def submit_transaction(user_id: int = Form(...), amount: float = Form(...)):
    """
    Accepts user input from HTML form, applies fraud logic, stores in DB
    """
    if user_id <= 0 or amount <= 0:
        return HTMLResponse(content="<h3>Invalid input. User ID and Amount must be positive.</h3><a href='/submit-transaction'>Go back</a>", status_code=400)

    # Fraud logic
    risk = "HIGH" if amount > 5000 else "LOW"

    # Store in SQLite database
    try:
        conn = sqlite3.connect("transactions.db")
        cursor = conn.cursor()
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                risk TEXT
            )
        """)
        # Insert transaction
        cursor.execute(
            "INSERT INTO transactions (user_id, amount, risk) VALUES (?, ?, ?)",
            (user_id, amount, risk)
        )
        conn.commit()
    except Exception as e:
        return HTMLResponse(content=f"<h3>Database error: {e}</h3>", status_code=500)
    finally:
        conn.close()

    # Return result page
    return f"""
        <h3>Transaction Submitted!</h3>
        <p>User ID: {user_id}</p>
        <p>Amount: {amount}</p>
        <p>Risk: {risk}</p>
        <a href='/submit-transaction'>Submit another</a>
    """

# -----------------------
# Transaction model for API
# -----------------------
class Transaction(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID must be positive")
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")

# -----------------------
# POST /transaction API
# -----------------------
@app.post("/transaction")
def create_transaction(transaction: Transaction):
    # Fraud logic
    risk = "HIGH" if transaction.amount > 5000 else "LOW"

    # Store in SQLite database
    try:
        conn = sqlite3.connect("transactions.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                risk TEXT
            )
        """)
        cursor.execute(
            "INSERT INTO transactions (user_id, amount, risk) VALUES (?, ?, ?)",
            (transaction.user_id, transaction.amount, risk)
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

    return {
        "user_id": transaction.user_id,
        "amount": transaction.amount,
        "risk": risk
    }

# -----------------------
# GET /transactions/{user_id} API
# -----------------------
@app.get("/transactions/{user_id}")
def get_transactions(user_id: int):
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    try:
        conn = sqlite3.connect("transactions.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

    transactions = []
    for row in rows:
        transactions.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "amount": row["amount"],
            "risk": row["risk"]
        })

    return {"user_id": user_id, "transactions": transactions}
