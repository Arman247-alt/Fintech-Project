#python -m uvicorn main:app --reload
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3

# Initialize FastAPI app
app = FastAPI()

# Root route for health check
@app.get("/")
def root():
    return {"message": "SentinelStream API is running"}

# Transaction input model with validation
class Transaction(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID must be positive")
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")

# POST /transaction - create and store transaction
@app.post("/transaction")
def create_transaction(transaction: Transaction):
    # Fraud logic
    if transaction.amount > 5000:
        risk = "HIGH"
    else:
        risk = "LOW"

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

# GET /transactions/{user_id} - fetch transactions for a user
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
