import os
import math
import random
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

import models
import schemas
from database import engine, get_db, SessionLocal
import seed_indian_food
import seed_restaurants

# 1. Initialize Tables in Database
models.Base.metadata.create_all(bind=engine)

# 2. Seed initial data if empty
with SessionLocal() as session:
    if session.query(models.DBMenuItem).count() == 0:
        seed_indian_food.seed_database()
    if session.query(models.DBRestaurant).count() == 0:
        seed_restaurants.seed_restaurants_and_banners()

app = FastAPI(
    title="YumQuick v3 Backend API",
    description="Full-featured food delivery REST API supporting location, restaurants, multi-item cart, live tracking, and JWT auth.",
    version="3.0.0"
)

# -------------------------------------------------------------
# CORS Middleware (Universal mobile & web access)
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# JWT & Security Configuration
# -------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "yumquick-super-secret-jwt-key-2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 15
REFRESH_TOKEN_EXPIRE_DAYS = 60

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[models.DBUser]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        return db.query(models.DBUser).filter(models.DBUser.id == user_id).first()
    except Exception:
        return None

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> models.DBUser:
    user = get_current_user_optional(authorization, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required or expired."
        )
    return user

# -------------------------------------------------------------
# Distance & Location Helpers
# -------------------------------------------------------------
def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# -------------------------------------------------------------
# System & Root
# -------------------------------------------------------------
@app.get("/")
def home():
    return {
        "app": "YumQuick Backend API",
        "version": "3.0.0",
        "status": "online",
        "currency": "₹",
        "docs": "/docs"
    }

# =============================================================
# 1. AUTHENTICATION & SESSION ENDPOINTS
# =============================================================
@app.post("/auth/signup", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: schemas.UserSignup, db: Session = Depends(get_db)):
    if db.query(models.DBUser).filter(func.lower(models.DBUser.email) == user_data.email.lower()).first():
        raise HTTPException(status_code=400, detail="A user with this email already exists.")
    if db.query(models.DBUser).filter(models.DBUser.mobile == user_data.mobile).first():
        raise HTTPException(status_code=400, detail="A user with this mobile already exists.")

    new_user = models.DBUser(
        full_name=user_data.fullName,
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
        mobile=user_data.mobile,
        dob=user_data.dob
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user.id)
    refresh_token = create_refresh_token(new_user.id)

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=schemas.UserResponse(
            id=new_user.id,
            fullName=new_user.full_name,
            email=new_user.email,
            mobile=new_user.mobile,
            dob=new_user.dob,
            avatar_url=new_user.avatar_url
        )
    )

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    ident = (login_data.identifier or login_data.email or login_data.phone or login_data.mobile or "").strip()
    if not ident:
        raise HTTPException(status_code=400, detail="Please enter your email or phone number.")

    user = db.query(models.DBUser).filter(
        (func.lower(models.DBUser.email) == ident.lower()) | (models.DBUser.mobile == ident)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email/phone or password.")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=schemas.UserResponse(
            id=user.id,
            fullName=user.full_name,
            email=user.email,
            mobile=user.mobile,
            dob=user.dob,
            avatar_url=user.avatar_url
        )
    )

@app.post("/auth/refresh")
def refresh_token_endpoint(data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type.")
        user_id = int(payload.get("sub"))
        user = db.query(models.DBUser).filter(models.DBUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found.")
        
        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid.")

@app.post("/auth/logout")
def logout(current_user: models.DBUser = Depends(get_current_user)):
    return {"message": "Logged out successfully."}

@app.post("/auth/forgot-password")
def forgot_password(req: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    ident = req.identifier.strip()
    user = db.query(models.DBUser).filter(
        (func.lower(models.DBUser.email) == ident.lower()) | (models.DBUser.mobile == ident)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account registered with this email/mobile.")

    otp = str(random.randint(1000, 9999))
    otp_record = models.DBOtp(
        identifier=ident,
        otp_code=otp,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    db.add(otp_record)
    db.commit()

    return {
        "message": f"Verification code sent to {ident}.",
        "demo_otp": otp  # Included for seamless developer testing
    }

@app.post("/auth/verify-otp")
def verify_otp(req: schemas.VerifyOtpRequest, db: Session = Depends(get_db)):
    record = db.query(models.DBOtp).filter(
        models.DBOtp.identifier == req.identifier.strip(),
        models.DBOtp.otp_code == req.otp_code.strip(),
        models.DBOtp.is_used == False
    ).order_by(desc(models.DBOtp.id)).first()

    if not record or record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code.")

    record.is_used = True
    db.commit()

    reset_token = jwt.encode(
        {"sub": req.identifier.strip(), "action": "reset_password", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    return {"message": "OTP verified successfully.", "reset_token": reset_token}

@app.post("/auth/reset-password")
def reset_password(req: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(req.reset_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("action") != "reset_password":
            raise HTTPException(status_code=400, detail="Invalid reset token.")
    except Exception:
        raise HTTPException(status_code=400, detail="Reset token expired or invalid.")

    user = db.query(models.DBUser).filter(
        (func.lower(models.DBUser.email) == req.identifier.strip().lower()) | 
        (models.DBUser.mobile == req.identifier.strip())
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"message": "Password has been successfully reset. You can now log in."}

@app.post("/auth/change-password")
def change_password(
    req: schemas.ChangePasswordRequest,
    current_user: models.DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"message": "Password updated successfully."}

# =============================================================
# 2. USER PROFILE & SETTINGS
# =============================================================
@app.get("/users/me", response_model=schemas.UserResponse)
def get_my_profile(current_user: models.DBUser = Depends(get_current_user)):
    return schemas.UserResponse(
        id=current_user.id,
        fullName=current_user.full_name,
        email=current_user.email,
        mobile=current_user.mobile,
        dob=current_user.dob,
        avatar_url=current_user.avatar_url
    )

@app.patch("/users/me", response_model=schemas.UserResponse)
def update_my_profile(
    update_data: schemas.UserUpdate,
    current_user: models.DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if update_data.fullName is not None:
        current_user.full_name = update_data.fullName
    if update_data.mobile is not None:
        current_user.mobile = update_data.mobile
    if update_data.dob is not None:
        current_user.dob = update_data.dob
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url

    db.commit()
    db.refresh(current_user)
    return schemas.UserResponse(
        id=current_user.id,
        fullName=current_user.full_name,
        email=current_user.email,
        mobile=current_user.mobile,
        dob=current_user.dob,
        avatar_url=current_user.avatar_url
    )

@app.delete("/users/me")
def delete_my_account(current_user: models.DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current_user)
    db.commit()
    return {"message": "Your YumQuick account has been deleted permanently."}

# =============================================================
# 3. LOCATION & ADDRESS ENDPOINTS
# =============================================================
@app.get("/location/reverse-geocode", response_model=schemas.LocationReverseGeocodeResponse)
def reverse_geocode(lat: float = Query(...), lng: float = Query(...)):
    # Standard reverse geocoder fallback simulation for India
    return schemas.LocationReverseGeocodeResponse(
        formatted_address=f"12th Main Rd, Indiranagar, Bengaluru, Karnataka 560038",
        house="Flat 101",
        street="12th Main Road",
        area="Indiranagar",
        city="Bengaluru",
        pincode="560038",
        lat=lat,
        lng=lng
    )

@app.get("/location/autocomplete", response_model=List[schemas.LocationAutocompleteItem])
def autocomplete_location(q: str = Query(..., min_length=1)):
    # Sample real-world area suggestions in Bengaluru & major hubs
    areas = [
        {"place_id": "p1", "primary_text": "Indiranagar", "secondary_text": "Bengaluru, Karnataka", "lat": 12.9784, "lng": 77.6408},
        {"place_id": "p2", "primary_text": "Koramangala 5th Block", "secondary_text": "Bengaluru, Karnataka", "lat": 12.9352, "lng": 77.6245},
        {"place_id": "p3", "primary_text": "HSR Layout Sector 1", "secondary_text": "Bengaluru, Karnataka", "lat": 12.9121, "lng": 77.6446},
        {"place_id": "p4", "primary_text": "Whitefield", "secondary_text": "Bengaluru, Karnataka", "lat": 12.9698, "lng": 77.7500},
        {"place_id": "p5", "primary_text": "MG Road", "secondary_text": "Bengaluru, Karnataka", "lat": 12.9756, "lng": 77.6066},
        {"place_id": "p6", "primary_text": "Jayanagar 4th Block", "secondary_text": "Bengaluru, Karnataka", "lat": 12.9299, "lng": 77.5834},
    ]
    filtered = [a for a in areas if q.lower() in a["primary_text"].lower() or q.lower() in a["secondary_text"].lower()]
    return filtered if filtered else areas[:3]

@app.get("/location/serviceability", response_model=schemas.LocationServiceabilityResponse)
def check_serviceability(lat: float = Query(...), lng: float = Query(...)):
    # Serviceable within 30km radius of Bengaluru Central (12.9716, 77.5946)
    dist = calculate_distance_km(lat, lng, 12.9716, 77.5946)
    if dist <= 35.0:
        return schemas.LocationServiceabilityResponse(
            serviceable=True,
            city="Bengaluru",
            delivery_fee=25.0 if dist < 5.0 else 35.0,
            estimated_time_mins=25 if dist < 5.0 else 40,
            message="Delivering delicious food to your area!"
        )
    return schemas.LocationServiceabilityResponse(
        serviceable=False,
        city="Unknown",
        delivery_fee=0.0,
        estimated_time_mins=0,
        message="We don't deliver to this location yet. You can still browse our menu!"
    )

@app.get("/addresses", response_model=List[schemas.AddressResponse])
def get_user_addresses(current_user: models.DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.DBAddress).filter(models.DBAddress.user_id == current_user.id).all()

@app.post("/addresses", response_model=schemas.AddressResponse, status_code=status.HTTP_201_CREATED)
def add_address(
    addr: schemas.AddressCreate,
    current_user: models.DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if addr.is_default:
        db.query(models.DBAddress).filter(models.DBAddress.user_id == current_user.id).update({"is_default": False})

    new_addr = models.DBAddress(
        user_id=current_user.id,
        label=addr.label,
        lat=addr.lat,
        lng=addr.lng,
        house=addr.house,
        street=addr.street,
        landmark=addr.landmark,
        city=addr.city,
        pincode=addr.pincode,
        contact=addr.contact,
        is_default=addr.is_default
    )
    db.add(new_addr)
    db.commit()
    db.refresh(new_addr)
    return new_addr

@app.patch("/addresses/{addr_id}", response_model=schemas.AddressResponse)
def update_address(
    addr_id: int,
    addr: schemas.AddressUpdate,
    current_user: models.DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = db.query(models.DBAddress).filter(
        models.DBAddress.id == addr_id,
        models.DBAddress.user_id == current_user.id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Address not found.")

    if addr.is_default:
        db.query(models.DBAddress).filter(models.DBAddress.user_id == current_user.id).update({"is_default": False})

    for key, value in addr.model_dump(exclude_unset=True).items():
        setattr(target, key, value)

    db.commit()
    db.refresh(target)
    return target

@app.delete("/addresses/{addr_id}")
def delete_address(
    addr_id: int,
    current_user: models.DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = db.query(models.DBAddress).filter(
        models.DBAddress.id == addr_id,
        models.DBAddress.user_id == current_user.id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Address not found.")
    db.delete(target)
    db.commit()
    return {"message": "Address deleted successfully."}

# =============================================================
# 4. RESTAURANTS & DISCOVERY
# =============================================================
@app.get("/restaurants", response_model=List[schemas.RestaurantResponse])
def get_restaurants(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    cuisine: Optional[str] = None,
    veg_only: bool = False,
    sort_by: Optional[str] = "rating",  # rating, delivery_time, distance
    db: Session = Depends(get_db)
):
    query = db.query(models.DBRestaurant)
    if veg_only:
        query = query.filter(models.DBRestaurant.is_pure_veg == True)
    if cuisine:
        query = query.filter(models.DBRestaurant.cuisines.ilike(f"%{cuisine}%"))

    restaurants = query.all()
    results = []
    user_lat = lat if lat is not None else 12.9716
    user_lng = lng if lng is not None else 77.5946

    for r in restaurants:
        distance = calculate_distance_km(user_lat, user_lng, r.lat, r.lng)
        eta = int(20 + (distance * 3))
        r_resp = schemas.RestaurantResponse(
            id=r.id,
            name=r.name,
            cover_url=r.cover_url,
            cuisines=r.cuisines,
            rating=r.rating,
            rating_count=r.rating_count,
            lat=r.lat,
            lng=r.lng,
            open_time=r.open_time,
            close_time=r.close_time,
            min_order=r.min_order,
            delivery_radius_km=r.delivery_radius_km,
            base_delivery_fee=r.base_delivery_fee,
            is_open=r.is_open,
            is_pure_veg=r.is_pure_veg,
            distance_km=distance,
            delivery_time_mins=eta
        )
        results.append(r_resp)

    if sort_by == "distance":
        results.sort(key=lambda x: x.distance_km or 999)
    elif sort_by == "delivery_time":
        results.sort(key=lambda x: x.delivery_time_mins or 999)
    else:
        results.sort(key=lambda x: x.rating, reverse=True)

    return results

@app.get("/restaurants/{rest_id}", response_model=schemas.RestaurantDetailResponse)
def get_restaurant_detail(
    rest_id: int,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    db: Session = Depends(get_db)
):
    r = db.query(models.DBRestaurant).filter(models.DBRestaurant.id == rest_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    user_lat = lat if lat is not None else 12.9716
    user_lng = lng if lng is not None else 77.5946
    distance = calculate_distance_km(user_lat, user_lng, r.lat, r.lng)
    eta = int(20 + (distance * 3))

    dishes = db.query(models.DBMenuItem).filter(models.DBMenuItem.restaurant_id == rest_id).all()
    grouped: dict[str, List[schemas.MenuItemResponse]] = {}
    for d in dishes:
        if d.category not in grouped:
            grouped[d.category] = []
        grouped[d.category].append(schemas.MenuItemResponse.model_validate(d))

    return schemas.RestaurantDetailResponse(
        id=r.id,
        name=r.name,
        cover_url=r.cover_url,
        cuisines=r.cuisines,
        rating=r.rating,
        rating_count=r.rating_count,
        lat=r.lat,
        lng=r.lng,
        open_time=r.open_time,
        close_time=r.close_time,
        min_order=r.min_order,
        delivery_radius_km=r.delivery_radius_km,
        base_delivery_fee=r.base_delivery_fee,
        is_open=r.is_open,
        is_pure_veg=r.is_pure_veg,
        distance_km=distance,
        delivery_time_mins=eta,
        menu_categories=grouped
    )

@app.get("/restaurants/{rest_id}/menu", response_model=List[schemas.MenuItemResponse])
def get_restaurant_menu(rest_id: int, db: Session = Depends(get_db)):
    return db.query(models.DBMenuItem).filter(models.DBMenuItem.restaurant_id == rest_id).all()

# =============================================================
# 5. MENU & DISHES
# =============================================================
@app.get("/menu/categories")
def get_categories(db: Session = Depends(get_db)):
    rows = db.query(models.DBMenuItem.category).distinct().all()
    return [r[0] for r in rows]

@app.get("/menu/stats")
def get_menu_stats(db: Session = Depends(get_db)):
    total = db.query(models.DBMenuItem).count()
    breakdown = db.query(models.DBMenuItem.category, func.count(models.DBMenuItem.id)).group_by(models.DBMenuItem.category).all()
    return {
        "total_items": total,
        "categories": {cat: cnt for cat, cnt in breakdown}
    }

@app.get("/menu", response_model=List[schemas.MenuItemResponse])
def get_all_menu_items(
    category: Optional[str] = None,
    restaurant_id: Optional[int] = None,
    search: Optional[str] = None,
    is_veg: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(models.DBMenuItem)
    if restaurant_id is not None:
        query = query.filter(models.DBMenuItem.restaurant_id == restaurant_id)
    if category:
        query = query.filter(models.DBMenuItem.category.ilike(f"%{category}%"))
    if is_veg is not None:
        query = query.filter(models.DBMenuItem.is_veg == is_veg)
    if search:
        query = query.filter(
            (models.DBMenuItem.name.ilike(f"%{search}%")) |
            (models.DBMenuItem.description.ilike(f"%{search}%"))
        )
    return query.offset(offset).limit(limit).all()

@app.get("/menu/{item_id}", response_model=schemas.MenuItemResponse)
def get_single_menu_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Dish not found.")
    return item

@app.post("/menu", response_model=schemas.MenuItemResponse, status_code=status.HTTP_201_CREATED)
def create_menu_item(item: schemas.MenuItemCreate, db: Session = Depends(get_db)):
    db_item = models.DBMenuItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.patch("/menu/{item_id}", response_model=schemas.MenuItemResponse)
def update_menu_item(item_id: int, item_update: schemas.MenuItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Dish not found.")
    for key, val in item_update.model_dump(exclude_unset=True).items():
        setattr(db_item, key, val)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Dish not found.")
    db.delete(db_item)
    db.commit()
    return {"message": f"'{db_item.name}' deleted successfully."}

# =============================================================
# 6. CART QUOTE & SERVER BILLING
# =============================================================
@app.post("/cart/quote", response_model=schemas.CartQuoteResponse)
def calculate_cart_quote(quote_req: schemas.CartQuoteRequest, db: Session = Depends(get_db)):
    if not quote_req.items:
        return schemas.CartQuoteResponse(
            subtotal=0.0, discount=0.0, delivery_fee=0.0, tax=0.0, total=0.0, items_count=0
        )

    subtotal = 0.0
    item_ids = [it.item_id for it in quote_req.items]
    dishes = {d.id: d for d in db.query(models.DBMenuItem).filter(models.DBMenuItem.id.in_(item_ids)).all()}

    for it in quote_req.items:
        if it.item_id not in dishes:
            raise HTTPException(status_code=404, detail=f"Dish ID {it.item_id} no longer available.")
        dish = dishes[it.item_id]
        unit_price = dish.price
        if it.size == "Large":
            unit_price += 50.0
        elif it.size == "Medium":
            unit_price += 25.0
        subtotal += unit_price * it.quantity

    # Delivery fee based on distance
    delivery_fee = 25.0
    if quote_req.lat and quote_req.lng:
        dist = calculate_distance_km(quote_req.lat, quote_req.lng, 12.9716, 77.5946)
        delivery_fee = 20.0 if dist < 3.0 else 35.0

    # 5% Restaurant GST
    tax = round(subtotal * 0.05, 2)

    # Promo discount calculation
    discount = 0.0
    promo_msg = None
    promo_code = (quote_req.promo_code or "").upper().strip()

    if promo_code == "WELCOME50":
        discount = round(min(subtotal * 0.50, 100.0), 2)
        promo_msg = "50% OFF applied (up to ₹100)"
    elif promo_code == "BIRYANILOVER":
        discount = 50.0
        promo_msg = "Flat ₹50 OFF applied"
    elif promo_code == "CHAI20":
        discount = round(subtotal * 0.20, 2)
        promo_msg = "20% OFF applied"
    elif promo_code:
        promo_msg = "Invalid or expired promo code."

    grand_total = round(max(subtotal - discount + delivery_fee + tax, 0.0), 2)

    return schemas.CartQuoteResponse(
        subtotal=round(subtotal, 2),
        discount=discount,
        delivery_fee=delivery_fee,
        tax=tax,
        total=grand_total,
        currency="₹",
        promo_applied=promo_code if discount > 0 else None,
        promo_message=promo_msg,
        estimated_time_mins=30,
        items_count=sum(i.quantity for i in quote_req.items)
    )

@app.post("/promos/validate")
def validate_promo(code: str = Query(...)):
    code_upper = code.upper().strip()
    valid_promos = {
        "WELCOME50": {"discount": 50.0, "type": "percentage", "max_discount": 100.0, "min_order": 199.0},
        "BIRYANILOVER": {"discount": 100.0, "type": "flat", "min_order": 299.0},
        "CHAI20": {"discount": 20.0, "type": "percentage", "min_order": 99.0}
    }
    if code_upper in valid_promos:
        return {"valid": True, "code": code_upper, "details": valid_promos[code_upper]}
    return {"valid": False, "code": code_upper, "message": "Invalid coupon code."}

# =============================================================
# 7. MULTI-ITEM ORDERS & TRACKING
# =============================================================
@app.post("/orders", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    order_data: dict,  # Accepts both new multi-item format or legacy format
    current_user: Optional[models.DBUser] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Support backward compatibility if someone sends single {"item_id": 1, "quantity": 2}
    if "item_id" in order_data and "items" not in order_data:
        dish = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == order_data["item_id"]).first()
        if not dish:
            raise HTTPException(status_code=404, detail="Dish not found.")
        qty = order_data.get("quantity", 1)
        items_list = [{"item_id": dish.id, "quantity": qty, "size": "Regular"}]
        cust_name = order_data.get("customer_name", current_user.full_name if current_user else "Guest Customer")
    else:
        items_list = order_data.get("items", [])
        cust_name = order_data.get("customer_name") or (current_user.full_name if current_user else "Valued Customer")

    if not items_list:
        raise HTTPException(status_code=400, detail="Cannot place an order with zero items.")

    subtotal = 0.0
    created_items = []
    rest_id = order_data.get("restaurant_id")

    for raw_it in items_list:
        d_id = raw_it.get("item_id")
        qty = raw_it.get("quantity", 1)
        dish = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == d_id).first()
        if not dish:
            raise HTTPException(status_code=404, detail=f"Dish ID {d_id} not found.")
        if not dish.is_available:
            raise HTTPException(status_code=400, detail=f"'{dish.name}' is currently out of stock.")

        if not rest_id and dish.restaurant_id:
            rest_id = dish.restaurant_id

        unit_p = dish.price
        total_p = round(unit_p * qty, 2)
        subtotal += total_p

        created_items.append(
            models.DBOrderItem(
                item_id=dish.id,
                item_name=dish.name,
                quantity=qty,
                size=raw_it.get("size", "Regular"),
                addons=raw_it.get("addons"),
                notes=raw_it.get("notes"),
                unit_price=unit_p,
                total_price=total_p
            )
        )

    delivery_fee = 25.0
    tax = round(subtotal * 0.05, 2)
    discount = 0.0
    p_code = order_data.get("promo_code")
    if p_code and p_code.upper() == "WELCOME50":
        discount = round(min(subtotal * 0.50, 100.0), 2)

    grand_total = round(subtotal + delivery_fee + tax - discount, 2)
    order_num = f"YUM-{random.randint(10000, 99999)}"

    new_order = models.DBOrder(
        order_number=order_num,
        user_id=current_user.id if current_user else None,
        customer_name=cust_name,
        restaurant_id=rest_id,
        address_id=order_data.get("address_id"),
        delivery_address_text=order_data.get("delivery_address_text", "Current GPS Location"),
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        tax=tax,
        discount=discount,
        total_price=grand_total,
        promo_code=p_code,
        payment_method=order_data.get("payment_method", "UPI"),
        payment_status="paid",
        status="received",
        delivery_notes=order_data.get("delivery_notes"),
        driver_name="Rajesh Kumar",
        driver_phone="+91 98765 43210",
        driver_lat=12.9716,
        driver_lng=77.5946,
        eta_mins=28
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for it in created_items:
        it.order_id = new_order.id
        db.add(it)
    db.commit()
    db.refresh(new_order)

    return new_order

@app.get("/orders", response_model=List[schemas.OrderResponse])
def get_orders(
    status_filter: Optional[str] = Query(None, alias="status"),  # active, past
    current_user: Optional[models.DBUser] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    query = db.query(models.DBOrder)
    if current_user:
        query = query.filter(models.DBOrder.user_id == current_user.id)

    if status_filter == "active":
        query = query.filter(models.DBOrder.status.in_(["received", "preparing", "out_for_delivery"]))
    elif status_filter == "past":
        query = query.filter(models.DBOrder.status.in_(["delivered", "cancelled"]))

    return query.order_by(desc(models.DBOrder.id)).all()

@app.get("/orders/{order_id}", response_model=schemas.OrderResponse)
def get_single_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.DBOrder).filter(models.DBOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order

@app.get("/orders/{order_id}/track", response_model=schemas.OrderTrackResponse)
def track_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.DBOrder).filter(models.DBOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    steps = [
        {"title": "Order Placed", "description": "We received your order", "done": True},
        {"title": "Preparing", "description": "Chef is preparing fresh food", "done": order.status in ["preparing", "out_for_delivery", "delivered"]},
        {"title": "Out for Delivery", "description": f"{order.driver_name} is on the way", "done": order.status in ["out_for_delivery", "delivered"]},
        {"title": "Delivered", "description": "Enjoy your delicious meal!", "done": order.status == "delivered"}
    ]

    return schemas.OrderTrackResponse(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        driver_name=order.driver_name,
        driver_phone=order.driver_phone,
        driver_lat=order.driver_lat,
        driver_lng=order.driver_lng,
        eta_mins=order.eta_mins,
        steps=steps
    )

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.DBOrder).filter(models.DBOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    if order.status not in ["received"]:
        raise HTTPException(status_code=400, detail="Cannot cancel: The kitchen has already started cooking.")
    
    order.status = "cancelled"
    db.commit()
    return {"message": "Order cancelled successfully. Refund initiated to your payment method."}

@app.post("/orders/{order_id}/reorder")
def reorder_past_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.DBOrder).filter(models.DBOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Past order not found.")
    
    items = []
    for it in order.items:
        items.append({
            "item_id": it.item_id,
            "item_name": it.item_name,
            "quantity": it.quantity,
            "size": it.size,
            "unit_price": it.unit_price
        })
    return {"message": "Items ready for cart.", "restaurant_id": order.restaurant_id, "items": items}

@app.patch("/orders/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(order_id: int, new_status: str, db: Session = Depends(get_db)):
    order = db.query(models.DBOrder).filter(models.DBOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order

# =============================================================
# 8. HOME FEED, BANNERS, FAVORITES & REVIEWS
# =============================================================
@app.get("/banners", response_model=List[schemas.BannerResponse])
def get_banners(db: Session = Depends(get_db)):
    return db.query(models.DBBanner).filter(models.DBBanner.is_active == True).all()

@app.get("/search/suggestions")
def search_suggestions(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    dish_names = [d[0] for d in db.query(models.DBMenuItem.name).filter(models.DBMenuItem.name.ilike(f"%{q}%")).limit(5).all()]
    rest_names = [r[0] for r in db.query(models.DBRestaurant.name).filter(models.DBRestaurant.name.ilike(f"%{q}%")).limit(3).all()]
    return {"dishes": dish_names, "restaurants": rest_names}

@app.get("/search/popular")
def popular_searches():
    return ["Biryani", "Butter Chicken", "Masala Dosa", "Hakka Noodles", "Paneer Butter Masala", "Chai", "Gulab Jamun"]

@app.get("/favorites", response_model=List[schemas.FavoriteResponse])
def get_favorites(current_user: models.DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.DBFavorite).filter(models.DBFavorite.user_id == current_user.id).all()

@app.post("/favorites", response_model=schemas.FavoriteResponse)
def add_favorite(
    fav: schemas.FavoriteCreate,
    current_user: models.DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.DBFavorite).filter(
        models.DBFavorite.user_id == current_user.id,
        models.DBFavorite.item_id == fav.item_id,
        models.DBFavorite.restaurant_id == fav.restaurant_id
    ).first()
    if existing:
        return existing
    new_fav = models.DBFavorite(user_id=current_user.id, item_id=fav.item_id, restaurant_id=fav.restaurant_id)
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return new_fav

@app.delete("/favorites/{fav_id}")
def remove_favorite(fav_id: int, current_user: models.DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = db.query(models.DBFavorite).filter(models.DBFavorite.id == fav_id, models.DBFavorite.user_id == current_user.id).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"message": "Removed from favorites."}

@app.get("/notifications", response_model=List[schemas.NotificationResponse])
def get_notifications(current_user: models.DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.DBNotification).filter(models.DBNotification.user_id == current_user.id).all()

@app.patch("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, current_user: models.DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(models.DBNotification).filter(models.DBNotification.id == notif_id, models.DBNotification.user_id == current_user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"message": "Notification marked as read."}

@app.post("/notifications/read-all")
def mark_all_notifications_read(current_user: models.DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(models.DBNotification).filter(models.DBNotification.user_id == current_user.id).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read."}

@app.post("/reviews", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
def post_review(
    rev: schemas.ReviewCreate,
    current_user: models.DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_rev = models.DBReview(
        user_id=current_user.id,
        restaurant_id=rev.restaurant_id,
        item_id=rev.item_id,
        rating=rev.rating,
        comment=rev.comment
    )
    db.add(new_rev)
    db.commit()
    db.refresh(new_rev)
    return new_rev

@app.get("/restaurants/{rest_id}/reviews", response_model=List[schemas.ReviewResponse])
def get_restaurant_reviews(rest_id: int, db: Session = Depends(get_db)):
    return db.query(models.DBReview).filter(models.DBReview.restaurant_id == rest_id).all()

@app.get("/home")
def get_home_feed(lat: Optional[float] = None, lng: Optional[float] = None, db: Session = Depends(get_db)):
    banners = db.query(models.DBBanner).filter(models.DBBanner.is_active == True).limit(5).all()
    categories = [r[0] for r in db.query(models.DBMenuItem.category).distinct().limit(8).all()]
    popular_dishes = db.query(models.DBMenuItem).order_by(desc(models.DBMenuItem.rating)).limit(10).all()
    restaurants = get_restaurants(lat=lat, lng=lng, db=db)[:6]
    return {
        "banners": [schemas.BannerResponse.model_validate(b) for b in banners],
        "categories": categories,
        "popular_dishes": [schemas.MenuItemResponse.model_validate(d) for d in popular_dishes],
        "nearby_restaurants": restaurants
    }

# =============================================================
# 9. ADMIN OVERVIEW & USER LIST
# =============================================================
@app.get("/admin/overview")
def get_admin_overview(db: Session = Depends(get_db)):
    total_users = db.query(models.DBUser).count()
    total_items = db.query(models.DBMenuItem).count()
    total_restaurants = db.query(models.DBRestaurant).count()
    total_orders = db.query(models.DBOrder).count()
    total_rev = db.query(func.sum(models.DBOrder.total_price)).scalar() or 0.0
    return {
        "status": "online",
        "total_users": total_users,
        "total_restaurants": total_restaurants,
        "total_dishes": total_items,
        "total_orders": total_orders,
        "total_revenue_inr": round(total_rev, 2)
    }

@app.get("/auth/users", response_model=List[schemas.UserResponse])
def list_all_users(db: Session = Depends(get_db)):
    users = db.query(models.DBUser).all()
    return [schemas.UserResponse.model_validate(u) for u in users]
