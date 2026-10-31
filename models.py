from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# -------------------------------------------------------------
# 1. USER & AUTHENTICATION
# -------------------------------------------------------------
class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    mobile = Column(String, unique=True, index=True, nullable=False)
    dob = Column(String, nullable=False)  # "YYYY-MM-DD"
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    addresses = relationship("DBAddress", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("DBOrder", back_populates="user")
    favorites = relationship("DBFavorite", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("DBNotification", back_populates="user", cascade="all, delete-orphan")


class DBOtp(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, index=True, nullable=False)  # email or mobile
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)


# -------------------------------------------------------------
# 2. ADDRESSES & LOCATION
# -------------------------------------------------------------
class DBAddress(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String, default="Home")  # Home, Work, Other
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    house = Column(String, nullable=False)
    street = Column(String, nullable=False)
    landmark = Column(String, nullable=True)
    city = Column(String, nullable=False, default="Bengaluru")
    pincode = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)

    user = relationship("DBUser", back_populates="addresses")


# -------------------------------------------------------------
# 3. RESTAURANTS
# -------------------------------------------------------------
class DBRestaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    cover_url = Column(String, nullable=False)
    cuisines = Column(String, nullable=False)  # "South Indian, Biryani, Street Food"
    rating = Column(Float, default=4.5)
    rating_count = Column(Integer, default=150)
    lat = Column(Float, nullable=False, default=12.9716)
    lng = Column(Float, nullable=False, default=77.5946)
    open_time = Column(String, default="07:00 AM")
    close_time = Column(String, default="11:00 PM")
    min_order = Column(Float, default=99.0)
    delivery_radius_km = Column(Float, default=12.0)
    base_delivery_fee = Column(Float, default=25.0)
    is_open = Column(Boolean, default=True)
    is_pure_veg = Column(Boolean, default=False)

    menu_items = relationship("DBMenuItem", back_populates="restaurant")
    orders = relationship("DBOrder", back_populates="restaurant")
    reviews = relationship("DBReview", back_populates="restaurant")


# -------------------------------------------------------------
# 4. MENU ITEMS
# -------------------------------------------------------------
class DBMenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    image_url = Column(String, nullable=True)
    is_veg = Column(Boolean, default=True)
    prep_time_mins = Column(Integer, default=20)
    rating = Column(Float, default=4.4)
    is_available = Column(Boolean, default=True)

    restaurant = relationship("DBRestaurant", back_populates="menu_items")
    order_items = relationship("DBOrderItem", back_populates="item")


# -------------------------------------------------------------
# 5. MULTI-ITEM ORDERS
# -------------------------------------------------------------
class DBOrder(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)
    delivery_address_text = Column(Text, nullable=True)
    
    subtotal = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=25.0)
    tax = Column(Float, default=0.0)  # GST
    discount = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    promo_code = Column(String, nullable=True)

    payment_method = Column(String, default="UPI / Online")
    payment_status = Column(String, default="paid")  # pending, paid, refunded
    status = Column(String, default="received")  # received -> preparing -> out_for_delivery -> delivered -> cancelled
    delivery_notes = Column(String, nullable=True)

    # Live Delivery Partner & Tracking
    driver_name = Column(String, default="Rajesh Kumar")
    driver_phone = Column(String, default="+91 98765 43210")
    driver_lat = Column(Float, default=12.9716)
    driver_lng = Column(Float, default=77.5946)
    eta_mins = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("DBUser", back_populates="orders")
    restaurant = relationship("DBRestaurant", back_populates="orders")
    items = relationship("DBOrderItem", back_populates="order", cascade="all, delete-orphan")


class DBOrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    size = Column(String, nullable=True)  # Regular, Medium, Large
    addons = Column(String, nullable=True)  # Comma-separated or JSON
    notes = Column(String, nullable=True)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("DBOrder", back_populates="items")
    item = relationship("DBMenuItem", back_populates="order_items")


# -------------------------------------------------------------
# 6. MARKETING, FAVORITES & NOTIFICATIONS
# -------------------------------------------------------------
class DBBanner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=True)
    image_url = Column(String, nullable=False)
    promo_code = Column(String, nullable=False)
    discount_percent = Column(Float, default=20.0)
    is_active = Column(Boolean, default=True)


class DBFavorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)

    user = relationship("DBUser", back_populates="favorites")


class DBNotification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, default="order")  # order, promo, account
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("DBUser", back_populates="notifications")


class DBReview(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    rating = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    restaurant = relationship("DBRestaurant", back_populates="reviews")
