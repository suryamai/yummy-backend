# 📋 Yummy Backend - Complete API Reference & Endpoints Catalog

This document lists **every route and endpoint** available in the `yummy-backend` API.

**Base URLs**:

- **Local Browser / Postman**: `http://127.0.0.1:8000`
- **Android Emulator**: `http://10.0.2.2:8000`
- **iOS Simulator**: `http://localhost:8000`
- **Physical Mobile Device (Wi-Fi)**: `http://192.168.1.11:8000`

---

## 📌 Master Route Table

| #   | Method   | Endpoint                    | Category       | Description                                         |
| :-- | :------- | :-------------------------- | :------------- | :-------------------------------------------------- |
| 1   | `GET`    | `/`                         | System         | Health check & system status                        |
| 2   | `GET`    | `/docs`                     | Docs           | Interactive Swagger UI documentation                |
| 3   | `GET`    | `/redoc`                    | Docs           | ReDoc UI documentation                              |
| 4   | `GET`    | `/openapi.json`             | Docs           | Raw OpenAPI specification JSON                      |
| 5   | `POST`   | `/auth/signup`              | Authentication | Register new user account                           |
| 6   | `POST`   | `/auth/login`               | Authentication | Login with email or phone + password                |
| 7   | `GET`    | `/auth/users`               | Authentication | View all registered users (Admin / Inspection)      |
| 8   | `GET`    | `/admin/overview`           | Admin          | Real-time counts of users, dishes, orders & revenue |
| 9   | `GET`    | `/menu/categories`          | Menu           | Get list of all distinct food categories            |
| 8   | `GET`    | `/menu/stats`               | Menu           | Get total dish count & category breakdown           |
| 9   | `GET`    | `/menu`                     | Menu           | Get dishes (supports category, search, pagination)  |
| 10  | `GET`    | `/menu/{item_id}`           | Menu           | Get single dish details by its ID                   |
| 11  | `POST`   | `/menu`                     | Menu (Admin)   | Add a new dish to the database                      |
| 12  | `PATCH`  | `/menu/{item_id}`           | Menu (Admin)   | Update price, availability, or details              |
| 13  | `DELETE` | `/menu/{item_id}`           | Menu (Admin)   | Delete a dish from the database                     |
| 14  | `POST`   | `/orders`                   | Orders         | Place a new food order                              |
| 15  | `GET`    | `/orders`                   | Orders         | View all placed orders with dish details            |
| 16  | `PATCH`  | `/orders/{order_id}/status` | Orders         | Update status (received, preparing, delivered)      |

---

## 🔐 1. Authentication Endpoints

### 1.1 User Signup

- **URL**: `POST /auth/signup`
- **Status Code**: `201 Created`
- **Description**: Registers a new user. Checks for duplicate emails or phone numbers. Hashes password with bcrypt.
- **Request Body**:

```json
{
  "fullName": "Jayasurya M",
  "email": "jaya@example.com",
  "password": "Password123!",
  "mobile": "9876543210",
  "dob": "2000-05-15"
}
```

- **Response**:

```json
{
  "id": 1,
  "fullName": "Jayasurya M",
  "email": "jaya@example.com",
  "mobile": "9876543210",
  "dob": "2000-05-15"
}
```

- **Errors**: `400 Bad Request` if email or mobile is already registered.

---

### 1.2 User Login

- **URL**: `POST /auth/login`
- **Status Code**: `200 OK`
- **Description**: Authenticates user using **either** email OR mobile/phone number, plus password.
- **Request Body (Option A - with Email)**:

```json
{
  "email": "jaya@example.com",
  "password": "Password123!"
}
```

- **Request Body (Option B - with Phone)**:

```json
{
  "phone": "9876543210",
  "password": "Password123!"
}
```

- **Response**:

```json
{
  "message": "Welcome back, Jayasurya M! Login successful. 🎉",
  "user": {
    "id": 1,
    "fullName": "Jayasurya M",
    "email": "jaya@example.com",
    "mobile": "9876543210",
    "dob": "2000-05-15"
  }
}
```

- **Errors**: `401 Unauthorized` if invalid credentials.

---

## 🍛 2. Menu Endpoints (540+ Dishes)

### 2.1 Get All Categories

- **URL**: `GET /menu/categories`
- **Status Code**: `200 OK`
- **Description**: Returns all unique category names (ideal for tabs/chips in mobile app).
- **Response**:

```json
[
  "South Indian",
  "North Indian",
  "Biryani & Rice",
  "Tandoor & Starters",
  "Street Food & Chaat",
  "Breads & Roti",
  "Sweets & Desserts",
  "Beverages & Drinks",
  "Indo-Chinese",
  "Regional Specials"
]
```

---

### 2.2 Get Menu Statistics

- **URL**: `GET /menu/stats`
- **Status Code**: `200 OK`
- **Response**:

```json
{
  "total_items": 540,
  "categories": {
    "South Indian": 110,
    "North Indian": 60,
    "Street Food & Chaat": 60,
    "Biryani & Rice": 50,
    "Tandoor & Starters": 50,
    "Sweets & Desserts": 50,
    "Beverages & Drinks": 50,
    "Indo-Chinese": 38,
    "Regional Specials": 37,
    "Breads & Roti": 35
  }
}
```

---

### 2.3 Get Dishes (Search, Filter & Pagination)

- **URL**: `GET /menu`
- **Status Code**: `200 OK`
- **Query Parameters**:
  - `category`: Filter by category name (e.g. `?category=South Indian`)
  - `search`: Search keyword matching name or description (e.g. `?search=biryani`)
  - `limit`: Number of items to return (default: `50`)
  - `offset`: Starting index for pagination (default: `0`)
- **Example**: `/menu?category=Biryani%20%26%20Rice&limit=10`
- **Response**:

```json
[
  {
    "id": 1,
    "name": "Steamed Idli (2 pcs)",
    "description": "Soft, fluffy steamed rice cakes served with coconut chutney & sambar",
    "price": 40.0,
    "category": "South Indian",
    "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop",
    "is_available": true
  }
]
```

---

### 2.4 Get Single Dish by ID

- **URL**: `GET /menu/{item_id}`
- **Status Code**: `200 OK`
- **Example**: `GET /menu/61`
- **Response**:

```json
{
  "id": 61,
  "name": "Chettinad Chicken Curry",
  "description": "Fiery Tamil Nadu chicken curry cooked with freshly roasted 14 whole spices",
  "price": 240.0,
  "category": "South Indian",
  "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop",
  "is_available": true
}
```

- **Errors**: `404 Not Found` if `item_id` does not exist.

---

### 2.5 Add New Dish (Admin)

- **URL**: `POST /menu`
- **Status Code**: `201 Created`
- **Request Body**:

```json
{
  "name": "Paneer Butter Masala Special",
  "description": "Rich cottage cheese in cashew butter sauce",
  "price": 250.0,
  "category": "North Indian",
  "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7",
  "is_available": true
}
```

---

### 2.6 Partially Update Dish (Admin)

- **URL**: `PATCH /menu/{item_id}`
- **Status Code**: `200 OK`
- **Description**: Update only the fields you send (e.g. price change or mark out of stock).
- **Request Body**:

```json
{
  "price": 260.0,
  "is_available": false
}
```

---

### 2.7 Delete Dish (Admin)

- **URL**: `DELETE /menu/{item_id}`
- **Status Code**: `200 OK`
- **Response**:

```json
{
  "message": "'Dish Name' has been successfully deleted from the database."
}
```

---

## 🛒 3. Order Management Endpoints

### 3.1 Place a New Order

- **URL**: `POST /orders`
- **Status Code**: `201 Created`
- **Request Body**:

```json
{
  "customer_name": "Jayasurya M",
  "item_id": 61,
  "quantity": 2
}
```

- **Validation Rules**:
  - Checks if `item_id` exists (`404` if not found).
  - Checks if dish `is_available` is `true` (`400` if out of stock).
  - Automatically calculates `total_price = dish.price * quantity`.
  - Sets initial status to `"received"`.
- **Response**:

```json
{
  "id": 1,
  "customer_name": "Jayasurya M",
  "quantity": 2,
  "total_price": 480.0,
  "status": "received",
  "item_id": 61,
  "item": {
    "id": 61,
    "name": "Chettinad Chicken Curry",
    "description": "Fiery Tamil Nadu chicken curry cooked with freshly roasted 14 whole spices",
    "price": 240.0,
    "category": "South Indian",
    "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop",
    "is_available": true
  }
}
```

---

### 3.2 View All Orders (Order History)

- **URL**: `GET /orders`
- **Status Code**: `200 OK`
- **Response**: Array of all placed orders with nested dish information.

---

### 3.3 Update Order Status

- **URL**: `PATCH /orders/{order_id}/status?new_status=preparing`
- **Status Code**: `200 OK`
- **Query Parameter**:
  - `new_status`: e.g. `"received"`, `"preparing"`, `"out_for_delivery"`, `"delivered"`
- **Response**: Updated order object.
