from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# -------------------------------------------------------------
# 1. AUTHENTICATION & USER SCHEMAS
# -------------------------------------------------------------
class UserSignup(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=100, example="Jayasurya M")
    email: EmailStr = Field(..., example="jaya@example.com")
    password: str = Field(..., min_length=6, max_length=100, example="Secret123!")
    mobile: str = Field(..., min_length=10, max_length=15, example="9876543210")
    dob: str = Field(..., example="2000-05-15", description="YYYY-MM-DD")

class UserLogin(BaseModel):
    identifier: Optional[str] = Field(None, description="Email OR Mobile number")
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    id: int
    fullName: str
    email: str
    mobile: str
    dob: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserUpdate(BaseModel):
    fullName: Optional[str] = None
    mobile: Optional[str] = None
    dob: Optional[str] = None
    avatar_url: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    identifier: str = Field(..., description="Registered Email or Mobile")

class VerifyOtpRequest(BaseModel):
    identifier: str
    otp_code: str = Field(..., min_length=4, max_length=6)

class ResetPasswordRequest(BaseModel):
    identifier: str
    reset_token: str
    new_password: str = Field(..., min_length=6)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


# -------------------------------------------------------------
# 2. ADDRESS & LOCATION SCHEMAS
# -------------------------------------------------------------
class AddressCreate(BaseModel):
    label: str = Field(default="Home", example="Home")  # Home, Work, Other
    lat: float = Field(..., example=12.9716)
    lng: float = Field(..., example=77.5946)
    house: str = Field(..., example="Flat 402, Sunshine Apts")
    street: str = Field(..., example="12th Main Road, Indiranagar")
    landmark: Optional[str] = Field(None, example="Near Metro Station")
    city: str = Field(default="Bengaluru", example="Bengaluru")
    pincode: str = Field(..., example="560038")
    contact: str = Field(..., example="9876543210")
    is_default: bool = False

class AddressUpdate(BaseModel):
    label: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    house: Optional[str] = None
    street: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    contact: Optional[str] = None
    is_default: Optional[bool] = None

class AddressResponse(AddressCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class LocationReverseGeocodeResponse(BaseModel):
    formatted_address: str
    house: Optional[str] = None
    street: str
    area: str
    city: str
    pincode: str
    lat: float
    lng: float

class LocationAutocompleteItem(BaseModel):
    place_id: str
    primary_text: str
    secondary_text: str
    lat: float
    lng: float

class LocationServiceabilityResponse(BaseModel):
    serviceable: bool
    city: str
    delivery_fee: float
    estimated_time_mins: int
    message: str


# -------------------------------------------------------------
# 3. RESTAURANT & MENU SCHEMAS
# -------------------------------------------------------------
class MenuItemCreate(BaseModel):
    restaurant_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: str
    image_url: Optional[str] = None
    is_veg: bool = True
    prep_time_mins: int = 20
    is_available: bool = True

class MenuItemResponse(MenuItemCreate):
    id: int
    rating: float = 4.4

    class Config:
        from_attributes = True

class MenuItemUpdate(BaseModel):
    restaurant_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_veg: Optional[bool] = None
    prep_time_mins: Optional[int] = None
    is_available: Optional[bool] = None

class RestaurantResponse(BaseModel):
    id: int
    name: str
    cover_url: str
    cuisines: str
    rating: float
    rating_count: int
    lat: float
    lng: float
    open_time: str
    close_time: str
    min_order: float
    delivery_radius_km: float
    base_delivery_fee: float
    is_open: bool
    is_pure_veg: bool
    distance_km: Optional[float] = None
    delivery_time_mins: Optional[int] = None

    class Config:
        from_attributes = True

class RestaurantDetailResponse(RestaurantResponse):
    menu_categories: dict[str, List[MenuItemResponse]] = {}


# -------------------------------------------------------------
# 4. CART QUOTE & MULTI-ITEM ORDER SCHEMAS
# -------------------------------------------------------------
class CartItemInput(BaseModel):
    item_id: int
    quantity: int = Field(default=1, gt=0)
    size: Optional[str] = "Regular"
    addons: Optional[str] = None
    notes: Optional[str] = None

class CartQuoteRequest(BaseModel):
    restaurant_id: Optional[int] = None
    items: List[CartItemInput]
    promo_code: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class CartQuoteResponse(BaseModel):
    subtotal: float
    discount: float
    delivery_fee: float
    tax: float  # 5% GST
    total: float
    currency: str = "₹"
    promo_applied: Optional[str] = None
    promo_message: Optional[str] = None
    estimated_time_mins: int = 30
    items_count: int

class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    quantity: int
    size: Optional[str] = None
    addons: Optional[str] = None
    notes: Optional[str] = None
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class OrderCreateMulti(BaseModel):
    customer_name: Optional[str] = None
    restaurant_id: Optional[int] = None
    address_id: Optional[int] = None
    delivery_address_text: Optional[str] = None
    items: List[CartItemInput]
    promo_code: Optional[str] = None
    payment_method: str = "UPI"
    delivery_notes: Optional[str] = None

# Backward compatibility single-item order
class OrderCreate(BaseModel):
    customer_name: str
    item_id: int
    quantity: int = 1

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_name: str
    status: str
    subtotal: float
    delivery_fee: float
    tax: float
    discount: float
    total_price: float
    payment_method: str
    payment_status: str
    eta_mins: int
    created_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

class OrderTrackResponse(BaseModel):
    order_id: int
    order_number: str
    status: str  # received, preparing, out_for_delivery, delivered, cancelled
    driver_name: str
    driver_phone: str
    driver_lat: float
    driver_lng: float
    eta_mins: int
    steps: List[dict]  # Stepper statuses with timestamps


# -------------------------------------------------------------
# 5. DISCOVERY, REVIEWS, NOTIFICATIONS & FAVORITES
# -------------------------------------------------------------
class BannerResponse(BaseModel):
    id: int
    title: str
    subtitle: Optional[str] = None
    image_url: str
    promo_code: str
    discount_percent: float

    class Config:
        from_attributes = True

class FavoriteCreate(BaseModel):
    item_id: Optional[int] = None
    restaurant_id: Optional[int] = None

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    item_id: Optional[int] = None
    restaurant_id: Optional[int] = None

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    restaurant_id: Optional[int] = None
    item_id: Optional[int] = None
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None

class ReviewResponse(ReviewCreate):
    id: int
    user_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
