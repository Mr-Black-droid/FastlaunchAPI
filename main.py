from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles 
import os
from typing import List
import sqlite3

app = FastAPI(
    title="FastLaunch API",
    description="Professional Launch Service API with Auth, CRUD, and Persistent Storage.",
    version="1.0.0"
)

security = HTTPBasic()
DATABASE = "launch_service.db"

class LaunchOrder(BaseModel):
    customer_name: str = Field(..., example="NASA")
    rocket_type: str = Field(..., example="Falcon 9")
    rideshare: bool = Field(..., example=True)

class OrderResponse(BaseModel):
    id: int
    customer: str
    rocket: str
    price: float
    is_rideshare: bool

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  customer TEXT, rocket TEXT, price REAL, is_rideshare INTEGER)''')
    conn.commit()
    conn.close()

init_db()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = os.getenv("API_USER", "alvin") 
    correct_pass = os.getenv("API_PASS", "mars2026")
    
    if credentials.username == correct_user and credentials.password == correct_pass:
        return credentials.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized access to Mission Control",
        headers={"WWW-Authenticate": "Basic"},
    )

def calculate_price(rocket: str, rideshare: bool) -> float:
    prices = {"Falcon 9": 67000000.0, "Falcon Heavy": 97000000.0}
    if rocket not in prices:
        raise HTTPException(status_code=400, detail=f"Rocket '{rocket}' not available.")
    
    base = prices[rocket]
    return base * 0.90 if rideshare else base

@app.get("/products", tags=["General"])
def list_products():
    return {"fleet": [{"name": "Falcon 9", "price": 67000000}, {"name": "Falcon Heavy", "price": 97000000}]}

@app.post("/orders", status_code=201, tags=["Missions"])
def create_order(order: LaunchOrder, user: str = Depends(get_current_user)):
    final_price = calculate_price(order.rocket_type, order.rideshare)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO orders (customer, rocket, price, is_rideshare) VALUES (?, ?, ?, ?)',
              (order.customer_name, order.rocket_type, final_price, 1 if order.rideshare else 0))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"order_id": new_id, "price": final_price}

@app.get("/orders", response_model=List[OrderResponse], tags=["Missions"])
def read_orders():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "customer": r[1], "rocket": r[2], "price": r[3], "is_rideshare": bool(r[4])} for r in rows]

@app.delete("/orders/{order_id}", tags=["Missions"])
def delete_order(order_id: int, user: str = Depends(get_current_user)):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('DELETE FROM orders WHERE id=?', (order_id,))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Mission scrubbed."}

app.mount("/", StaticFiles(directory=".", html=True), name="static")