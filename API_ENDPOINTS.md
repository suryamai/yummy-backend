# 📋 YumQuick v3 - Complete API Reference & Endpoints Catalog (56 Endpoints)

This is the comprehensive master reference for all **56 endpoints** implemented in the **YumQuick v3 Backend** (FastAPI + Supabase PostgreSQL).

**Base URLs**:
- **Local Development**: `http://127.0.0.1:8000`
- **Render Cloud Production**: `https://yummy-backend-igrf.onrender.com`
- **Local Wi-Fi Mobile Testing**: `http://192.168.1.11:8000`

---

## 📌 Master Route Table

| # | Method | Endpoint | Category | Description |
|:--|:-------|:---------|:---------|:------------|
| 1 | `GET` | `/` | System | Health check & system status |
| 2 | `GET` | `/docs` | Docs | Interactive Swagger UI documentation |
| 3 | `GET` | `/redoc` | Docs | ReDoc UI documentation |
| 4 | `POST` | `/auth/signup` | Auth (P0) | Register new user + JWT access/refresh tokens |
| 5 | `POST` | `/auth/login` | Auth (P0) | Login via email/phone + JWT access/refresh tokens |
| 6 | `POST` | `/auth/refresh` | Auth (P0) | Issue fresh access token using refresh token |
| 7 | `POST` | `/auth/logout` | Auth (P0) | Invalidate user session tokens |
| 8 | `POST` | `/auth/forgot-password` | Auth (P1) | Send 4-digit verification OTP to email/mobile |
| 9 | `POST` | `/auth/verify-otp` | Auth (P1) | Verify OTP and return reset token |
| 10 | `POST` | `/auth/reset-password` | Auth (P1) | Set new password with reset token |
| 11 | `POST` | `/auth/change-password` | Auth (P1) | Change password while logged in |
| 12 | `GET` | `/auth/users` | Admin | View all registered user profiles |
| 13 | `GET` | `/users/me` | Profile (P0) | Get authenticated user profile (name, email, phone, DOB, avatar) |
| 14 | `PATCH` / `PUT` | `/users/me` | Profile (P0) | Update name, email, phone/mobile, DOB, photo/avatar URL |
| 15 | `POST` | `/users/me/avatar` | Profile (P0) | Upload profile picture file (`multipart/form-data`) |
| 16 | `DELETE` | `/users/me` | Profile (P1) | Delete account permanently |
| 16 | `GET` | `/location/reverse-geocode` | Location (P0) | Convert lat/lng to formatted address |
| 17 | `GET` | `/location/autocomplete` | Location (P0) | Search address suggestions as user types |
| 18 | `GET` | `/location/serviceability` | Location (P0) | Check if lat/lng is deliverable + ETA & fee |
| 19 | `GET` | `/addresses` | Address (P0) | List user's saved delivery addresses |
| 20 | `POST` | `/addresses` | Address (P0) | Add new address (house, street, lat, lng, contact) |
| 21 | `PATCH` | `/addresses/{id}` | Address (P0) | Edit address or set as default |
| 22 | `DELETE` | `/addresses/{id}` | Address (P0) | Delete an address |
| 23 | `GET` | `/restaurants` | Restaurant (P0) | List nearby restaurants with distance, fee & ETA |
| 24 | `GET` | `/restaurants/{id}` | Restaurant (P0) | Restaurant details + menu grouped by category |
| 25 | `GET` | `/restaurants/{id}/menu` | Restaurant (P0) | Get dishes belonging to a restaurant |
| 26 | `GET` | `/menu` | Menu (P0) | Search/filter dishes (category, restaurant, veg, sort) |
| 27 | `GET` | `/menu/{id}` | Menu (P0) | Get single dish details by ID |
| 28 | `POST` | `/menu` | Menu (Admin) | Add a new dish to the catalog |
| 29 | `PATCH` | `/menu/{id}` | Menu (Admin) | Update price, availability, or dish details |
| 30 | `DELETE` | `/menu/{id}` | Menu (Admin) | Delete a dish |
| 31 | `GET` | `/menu/categories` | Menu | List all distinct food categories |
| 32 | `GET` | `/menu/stats` | Menu | Total dishes count & category breakdown |
| 33 | `POST` | `/cart/quote` | Cart (P0) | Server bill calculation (subtotal, fee, GST, promo, total in ₹) |
| 34 | `POST` | `/promos/validate` | Cart (P1) | Validate discount coupon code |
| 35 | `POST` | `/orders` | Orders (P0) | Place multi-item order with sizes, notes & address |
| 36 | `GET` | `/orders` | Orders (P0) | List user orders with `?status=active` or `?status=past` |
| 37 | `GET` | `/orders/{id}` | Orders (P0) | Get single order details with all line items |
| 38 | `GET` | `/orders/{id}/track` | Orders (P0) | Live order tracking with driver position, ETA & steps |
| 39 | `POST` | `/orders/{id}/cancel` | Orders (P0) | Cancel order before cooking starts |
| 40 | `POST` | `/orders/{id}/reorder` | Orders (P1) | Re-populate cart from past order |
| 41 | `PATCH` | `/orders/{id}/status` | Orders (Admin) | Update order status (received, preparing, out_for_delivery, delivered) |
| 42 | `GET` | `/home` | Discovery (P2) | Aggregated Home feed (banners, categories, popular, nearby) |
| 43 | `GET` | `/banners` | Discovery (P1) | Offer carousel banners for Home screen |
| 44 | `GET` | `/search/suggestions` | Discovery (P1) | Live autocomplete for dishes and restaurants |
| 45 | `GET` | `/search/popular` | Discovery (P1) | Trending search keywords |
| 46 | `GET` | `/favorites` | Favorites (P1) | List user's favorite dishes and restaurants |
| 47 | `POST` | `/favorites` | Favorites (P1) | Add dish or restaurant to favorites |
| 48 | `DELETE` | `/favorites/{id}` | Favorites (P1) | Remove from favorites |
| 49 | `GET` | `/notifications` | Notifications (P1) | List user notifications |
| 50 | `PATCH` | `/notifications/{id}/read`| Notifications (P1) | Mark a single notification as read |
| 51 | `POST` | `/notifications/read-all`| Notifications (P1) | Mark all notifications as read |
| 52 | `POST` | `/reviews` | Reviews (P1) | Submit rating & review for food or restaurant |
| 53 | `GET` | `/restaurants/{id}/reviews`| Reviews (P1) | Read reviews for a restaurant |
| 54 | `GET` | `/admin/overview` | Admin | Real-time counts of users, restaurants, orders & revenue |

---

## 🔐 1. Authentication & Profile Samples

### 1.1 Signup (`POST /auth/signup`)
```json
{
  "fullName": "Jayasurya M",
  "email": "jaya@example.com",
  "password": "Password123!",
  "mobile": "9876543210",
  "dob": "2000-05-15"
}
```
**Returns**: `access_token`, `refresh_token`, and user profile.

### 1.2 Login (`POST /auth/login`)
```json
{
  "email": "jaya@example.com",
  "password": "Password123!"
}
```

---

## 📍 2. Location & Address Samples

### 2.1 Serviceability Check (`GET /location/serviceability?lat=12.9716&lng=77.5946`)
**Returns**:
```json
{
  "serviceable": true,
  "city": "Bengaluru",
  "delivery_fee": 25.0,
  "estimated_time_mins": 25,
  "message": "Delivering delicious food to your area!"
}
```

### 2.2 Add Address (`POST /addresses`)
*Header: `Authorization: Bearer <access_token>`*
```json
{
  "label": "Home",
  "lat": 12.9784,
  "lng": 77.6408,
  "house": "Flat 301, Emerald Apts",
  "street": "100 Feet Road, Indiranagar",
  "landmark": "Opposite Toit",
  "city": "Bengaluru",
  "pincode": "560038",
  "contact": "9876543210",
  "is_default": true
}
```

---

## 🍛 3. Restaurants & Discovery Samples

### 3.1 Nearby Restaurants (`GET /restaurants?lat=12.9716&lng=77.5946&sort_by=rating`)
**Returns**: List of restaurants with computed `distance_km`, `delivery_time_mins`, ratings, cuisines, and cover photos.

### 3.2 Aggregated Home Screen Feed (`GET /home?lat=12.9716&lng=77.5946`)
**Returns**: Promo banners, top categories, popular dishes, and nearby restaurants in a single ultra-fast network call!

---

## 🛒 4. Cart Quote & Multi-Item Order Samples

### 4.1 Server Bill Calculation (`POST /cart/quote`)
```json
{
  "restaurant_id": 1,
  "lat": 12.9716,
  "lng": 77.5946,
  "promo_code": "WELCOME50",
  "items": [
    { "item_id": 1, "quantity": 2, "size": "Regular" },
    { "item_id": 10, "quantity": 1, "size": "Regular" }
  ]
}
```
**Returns**:
```json
{
  "subtotal": 150.0,
  "discount": 75.0,
  "delivery_fee": 20.0,
  "tax": 7.5,
  "total": 102.5,
  "currency": "₹",
  "promo_applied": "WELCOME50",
  "promo_message": "50% OFF applied (up to ₹100)",
  "estimated_time_mins": 30,
  "items_count": 3
}
```

### 4.2 Place Multi-Item Order (`POST /orders`)
```json
{
  "restaurant_id": 1,
  "address_id": 1,
  "delivery_address_text": "Flat 301, Emerald Apts, Indiranagar",
  "payment_method": "UPI",
  "promo_code": "WELCOME50",
  "delivery_notes": "Please leave at door and don't ring bell",
  "items": [
    { "item_id": 1, "quantity": 2, "size": "Regular" },
    { "item_id": 10, "quantity": 1, "size": "Regular" }
  ]
}
```

### 4.3 Live Order Tracking (`GET /orders/{id}/track`)
**Returns**:
```json
{
  "order_id": 1,
  "order_number": "YUM-49210",
  "status": "out_for_delivery",
  "driver_name": "Rajesh Kumar",
  "driver_phone": "+91 98765 43210",
  "driver_lat": 12.9734,
  "driver_lng": 77.6012,
  "eta_mins": 14,
  "steps": [
    { "title": "Order Placed", "description": "We received your order", "done": true },
    { "title": "Preparing", "description": "Chef is preparing fresh food", "done": true },
    { "title": "Out for Delivery", "description": "Rajesh Kumar is on the way", "done": true },
    { "title": "Delivered", "description": "Enjoy your delicious meal!", "done": false }
  ]
}
```
