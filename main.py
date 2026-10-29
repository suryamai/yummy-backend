import bcrypt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas
from database import engine, get_db, SessionLocal
import seed_indian_food

# 1. Create all database tables on startup (menu_items, orders, users)
models.Base.metadata.create_all(bind=engine)

# 2. Seed initial 500+ Indian dishes if the database is empty
with SessionLocal() as session:
    if session.query(models.DBMenuItem).count() == 0:
        seed_indian_food.seed_database()

app = FastAPI(
    title="Yummy Restaurant API (Pan-India Menu & Orders)",
    description="Backend API featuring 500+ authentic Indian foods, street snacks, biryanis, drinks, and sweets.",
    version="2.2.0"
)

# -------------------------------------------------------------
# CORS Middleware (Crucial for Mobile & Web Applications)
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allows all frontends/mobile apps to connect
    allow_credentials=True,
    allow_methods=["*"],      # Allows GET, POST, PUT, PATCH, DELETE, OPTIONS
    allow_headers=["*"],      # Allows all headers
)

# -------------------------------------------------------------
# Password Hashing Helpers (bcrypt)
# -------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# -------------------------------------------------------------
# General Endpoints
# -------------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to Yummy Restaurant API! 🍔🍕🍛",
        "database": "SQLite (yummy.db) - Connected & Active",
        "docs_url": "/docs",
        "menu_url": "/menu"
    }

# -------------------------------------------------------------
# AUTHENTICATION ENDPOINTS (Signup & Login)
# -------------------------------------------------------------

# SIGNUP: Register new user
@app.post("/auth/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: schemas.UserSignup, db: Session = Depends(get_db)):
    existing_email = db.query(models.DBUser).filter(
        func.lower(models.DBUser.email) == user_data.email.lower()
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    existing_mobile = db.query(models.DBUser).filter(models.DBUser.mobile == user_data.mobile).first()
    if existing_mobile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this mobile number already exists."
        )

    hashed_pwd = hash_password(user_data.password)

    new_user = models.DBUser(
        full_name=user_data.fullName,
        email=user_data.email.lower(),
        hashed_password=hashed_pwd,
        mobile=user_data.mobile,
        dob=user_data.dob
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return schemas.UserResponse(
        id=new_user.id,
        fullName=new_user.full_name,
        email=new_user.email,
        mobile=new_user.mobile,
        dob=new_user.dob
    )

# LOGIN: Login using (email OR phone/mobile) + password
@app.post("/auth/login", response_model=schemas.LoginResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    account_id = (
        login_data.identifier or 
        login_data.email or 
        login_data.phone or 
        login_data.mobile
    )

    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an email or phone/mobile number to login."
        )

    clean_account_id = account_id.strip()

    user = db.query(models.DBUser).filter(
        (func.lower(models.DBUser.email) == clean_account_id.lower()) | 
        (models.DBUser.mobile == clean_account_id)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password."
        )

    return schemas.LoginResponse(
        message=f"Welcome back, {user.full_name}! Login successful. 🎉",
        user=schemas.UserResponse(
            id=user.id,
            fullName=user.full_name,
            email=user.email,
            mobile=user.mobile,
            dob=user.dob
        )
    )

# -------------------------------------------------------------
# MENU ENDPOINTS (500+ Indian Dishes)
# -------------------------------------------------------------

# STATS: Quick overview of menu counts by category
@app.get("/menu/stats")
def get_menu_stats(db: Session = Depends(get_db)):
    total = db.query(models.DBMenuItem).count()
    breakdown = db.query(models.DBMenuItem.category, func.count(models.DBMenuItem.id)).group_by(models.DBMenuItem.category).all()
    return {
        "total_items": total,
        "categories": {category: count for category, count in breakdown}
    }

# CATEGORIES: List all unique categories available
@app.get("/menu/categories")
def get_categories(db: Session = Depends(get_db)):
    rows = db.query(models.DBMenuItem.category).distinct().all()
    return [row[0] for row in rows]

# READ ALL: Fetch items with category filter, search query & pagination
@app.get("/menu", response_model=list[schemas.MenuItemResponse])
def get_all_menu_items(
    category: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(models.DBMenuItem)
    if category:
        query = query.filter(models.DBMenuItem.category.ilike(f"%{category}%"))
    if search:
        query = query.filter(
            (models.DBMenuItem.name.ilike(f"%{search}%")) | 
            (models.DBMenuItem.description.ilike(f"%{search}%"))
        )
    return query.offset(offset).limit(limit).all()

# READ ONE: Fetch single item by ID
@app.get("/menu/{item_id}", response_model=schemas.MenuItemResponse)
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with ID {item_id} not found."
        )
    return item

# CREATE: Add a new dish
@app.post("/menu", response_model=schemas.MenuItemResponse, status_code=status.HTTP_201_CREATED)
def create_menu_item(item: schemas.MenuItemCreate, db: Session = Depends(get_db)):
    db_item = models.DBMenuItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# UPDATE: Partially update an existing item
@app.patch("/menu/{item_id}", response_model=schemas.MenuItemResponse)
def update_menu_item(
    item_id: int, 
    item_update: schemas.MenuItemUpdate, 
    db: Session = Depends(get_db)
):
    db_item = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with ID {item_id} not found."
        )

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item

# DELETE: Remove an item
@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with ID {item_id} not found."
        )
    db.delete(item)
    db.commit()
    return {"message": f"'{item.name}' has been successfully deleted from the database."}

# -------------------------------------------------------------
# ORDER ENDPOINTS (Supports both /orders and /order)
# -------------------------------------------------------------

# CREATE: Place a new order
@app.post("/orders", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
@app.post("/order", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def place_order(order_data: schemas.OrderCreate, db: Session = Depends(get_db)):
    dish = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == order_data.item_id).first()
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot order: Dish with ID {order_data.item_id} does not exist."
        )

    if not dish.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sorry, '{dish.name}' is currently out of stock!"
        )

    calculated_total = round(dish.price * order_data.quantity, 2)

    new_order = models.DBOrder(
        customer_name=order_data.customer_name,
        item_id=order_data.item_id,
        quantity=order_data.quantity,
        total_price=calculated_total,
        status="received"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# READ ALL: View all orders
@app.get("/orders", response_model=list[schemas.OrderResponse])
@app.get("/order", response_model=list[schemas.OrderResponse], include_in_schema=False)
def get_all_orders(db: Session = Depends(get_db)):
    return db.query(models.DBOrder).all()

# READ ONE: Track single order by ID
@app.get("/orders/{order_id}", response_model=schemas.OrderResponse)
@app.get("/order/{order_id}", response_model=schemas.OrderResponse, include_in_schema=False)
def get_single_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.DBOrder).filter(models.DBOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    return order

# UPDATE STATUS: e.g. "received" -> "preparing" -> "delivered"
@app.patch("/orders/{order_id}/status", response_model=schemas.OrderResponse)
@app.patch("/order/{order_id}/status", response_model=schemas.OrderResponse, include_in_schema=False)
def update_order_status(order_id: int, new_status: str, db: Session = Depends(get_db)):
    order = db.query(models.DBOrder).filter(models.DBOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
