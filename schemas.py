from pydantic import BaseModel, Field, EmailStr

# -------------------------------------------------------------
# Menu Item Schemas
# -------------------------------------------------------------

class MenuItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Hyderabadi Chicken Dum Biryani")
    description: str | None = Field(None, max_length=500, example="Fragrant basmati rice layered with spiced marinated chicken and saffron")
    price: float = Field(..., gt=0, example=280.00)
    category: str = Field(..., example="Biryani & Rice")
    image_url: str | None = Field(None, example="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8")
    is_available: bool = True

class MenuItemResponse(MenuItemCreate):
    id: int

    class Config:
        from_attributes = True

class MenuItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    category: str | None = None
    image_url: str | None = None
    is_available: bool | None = None

# -------------------------------------------------------------
# Order Schemas
# -------------------------------------------------------------

class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=50, example="Surya")
    item_id: int = Field(..., gt=0, example=1)
    quantity: int = Field(default=1, gt=0, le=20, example=2)

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    quantity: int
    total_price: float
    status: str
    item_id: int
    item: MenuItemResponse

    class Config:
        from_attributes = True

# -------------------------------------------------------------
# User & Authentication Schemas
# -------------------------------------------------------------

class UserSignup(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=100, example="Jayasurya M")
    email: EmailStr = Field(..., example="jaya@example.com")
    password: str = Field(..., min_length=6, max_length=100, example="Secret123!")
    mobile: str = Field(..., min_length=10, max_length=15, example="9876543210")
    dob: str = Field(..., example="2000-05-15", description="Date of birth in YYYY-MM-DD format")

class UserLogin(BaseModel):
    identifier: str | None = Field(None, example="jaya@example.com", description="Enter your email OR phone/mobile number")
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    password: str = Field(..., min_length=1, example="Secret123!")

class UserResponse(BaseModel):
    id: int
    fullName: str
    email: str
    mobile: str
    dob: str

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    message: str
    user: UserResponse
