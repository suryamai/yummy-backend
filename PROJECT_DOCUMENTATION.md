# 📖 Yummy Backend - Complete System Architecture & Engineering Guide

Welcome to the official technical documentation for **Yummy Backend**.

This document explains **how the system works**, **the engineering decisions behind every component**, **the alternatives that exist in the software industry**, and **why this architecture was chosen**.

---

## 📑 Table of Contents

1. [Executive Summary & Purpose](#1-executive-summary--purpose)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [The Request Lifecycle (Step-by-Step)](#3-the-request-lifecycle-step-by-step)
4. [Deep-Dive: Why We Chose This Approach vs. Alternatives](#4-deep-dive-why-we-chose-this-approach-vs-alternatives)
   - [A. Web Framework: FastAPI vs. Flask vs. Django vs. Express (Node.js)](#a-web-framework-fastapi-vs-flask-vs-django-vs-express-nodejs)
   - [B. Database: SQLite vs. PostgreSQL vs. MongoDB (NoSQL)](#b-database-sqlite-vs-postgresql-vs-mongodb-nosql)
   - [C. Data Access: SQLAlchemy ORM vs. Raw SQL](#c-data-access-sqlalchemy-orm-vs-raw-sql)
   - [D. Validation: Pydantic vs. Manual Parsing](#d-validation-pydantic-vs-manual-parsing)
   - [E. Security: bcrypt Hashing vs. Plain/MD5/SHA](#e-security-bcrypt-hashing-vs-plainmd5sha)
5. [Codebase Organization & Separation of Concerns](#5-codebase-organization--separation-of-concerns)
6. [Database Schema & Entity Relationships](#6-database-schema--entity-relationships)
7. [Step-by-Step Guide: How to Start and Run the Project](#7-step-by-step-guide-how-to-start-and-run-the-project)
8. [Connecting to Mobile Applications (Android, iOS, Physical Devices)](#8-connecting-to-mobile-applications-android-ios-physical-devices)
9. [Troubleshooting & Common Pitfalls](#9-troubleshooting--common-pitfalls)
10. [Future Production Roadmap](#10-future-production-roadmap)

---

## 1. Executive Summary & Purpose

**Yummy Backend** is a high-performance RESTful API designed to power food ordering and restaurant discovery mobile/web applications.

### Key Capabilities:

- **Full Authentication System**: Secure user signup and login supporting dual identifiers (Email OR Mobile Number) with salted **bcrypt** password hashing.
- **Rich Catalog of 540+ Pan-Indian Food & Drink Items**: Categorized across 10 culinary traditions (South Indian, North Indian, Biryanis, Street Food, Tandoor, Indo-Chinese, Sweets, Beverages, etc.) with high-resolution imagery and Indian Rupee (INR) pricing.
- **Search, Filtering, and Pagination**: Fast search queries by keyword and category filters with offset/limit pagination.
- **Relational Order Management**: Real-time order placement that validates dish availability, computes prices accurately on the server, and links orders to dishes via Foreign Key relationships.
- **Cross-Platform Readiness (CORS)**: Preconfigured for mobile apps (Flutter, React Native, Native Android/iOS) and web SPAs.

---

## 2. End-to-End System Architecture

The project follows a **layered, decoupled architecture** separating HTTP delivery, business rules, data schemas, and persistence:

```
┌────────────────────────────────────────────────────────┐
│      Client Layer (Mobile App / Browser / Postman)      │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / JSON
                            ▼
┌────────────────────────────────────────────────────────┐
│              Uvicorn (ASGI Web Server)                 │
│         Listens on 0.0.0.0:8000 via TCP sockets        │
└───────────────────────────┬────────────────────────────┘
                            │ ASGI Event Loop
                            ▼
┌────────────────────────────────────────────────────────┐
│                      FastAPI                           │
│  ├── CORS Middleware (Cross-Origin Resource Sharing)   │
│  ├── Router (URL Matching: /auth, /menu, /orders)     │
│  └── Dependency Injection (get_db Session Lifecycle)   │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
   Validates Request JSON       Serializes Python Objects
              ▼                            ▲
┌───────────────────────────┐ ┌──────────────────────────┐
│      Pydantic Schemas     │ │     Pydantic Schemas     │
│       (schemas.py)        │ │       (schemas.py)       │
│  Type checks, constraints │ │   Response filtering     │
└─────────────┬─────────────┘ └────────────▲─────────────┘
              │                            │
              ▼                            │
┌────────────────────────────────────────────────────────┐
│               Business Logic & Security                │
│  - Password Hashing & Verification (bcrypt)            │
│  - Total Price Computation (Server-side calculation)   │
│  - Availability and Out-of-Stock Validation            │
└───────────────────────────┬────────────────────────────┘
                            │ Queries / Mutations
                            ▼
┌────────────────────────────────────────────────────────┐
│                 SQLAlchemy 2.0 ORM                     │
│                    (models.py)                         │
│  Translates Python objects into SQL queries & dialect  │
└───────────────────────────┬────────────────────────────┘
                            │ Relational Operations
                            ▼
┌────────────────────────────────────────────────────────┐
│                 SQLite Database (Disk)                 │
│                    (yummy.db)                          │
│   Tables: `users`, `menu_items`, `orders`              │
└────────────────────────────────────────────────────────┘
```

---

## 3. The Request Lifecycle (Step-by-Step)

To understand how the system executes code, consider what happens when a user places an order (`POST /orders`):

```
1. Mobile App sends HTTP POST with JSON body:
   { "customer_name": "Jayasurya", "item_id": 61, "quantity": 2 }

2. Uvicorn parses raw bytes from the network port into standard ASGI HTTP objects.

3. CORSMiddleware checks headers to confirm the mobile client's origin is permitted.

4. Dependency Injection (Depends(get_db)):
   FastAPI calls get_db() -> creates a dedicated SQLAlchemy database session for this request.

5. Pydantic Validation:
   FastAPI parses the JSON payload against schemas.OrderCreate.
   If "quantity" is negative or "item_id" is missing, FastAPI instantly stops
   execution and returns HTTP 422 Unprocessable Entity with exact error locations.

6. Route Handler Execution (place_order in main.py):
   a. DB query: Fetches DBMenuItem where id == 61 using the SQLAlchemy session.
   b. Validation: If dish not found -> returns HTTP 404.
   c. Stock check: If is_available == False -> returns HTTP 400 ("Out of stock").
   d. Business calculation: calculated_total = round(dish.price * quantity, 2).
      (NEVER trust client-provided totals; prices must be calculated on the backend!)
   e. DB insertion: Constructs DBOrder and commits to SQLite.

7. Response Serialization:
   SQLAlchemy returns the newly created DBOrder. FastAPI passes it to schemas.OrderResponse.
   Because from_attributes = True is set, Pydantic traverses the foreign-key
   relationship (order.item) and bundles the full dish details + image into the JSON.

8. Session Teardown:
   The finally block inside get_db() executes, closing the SQLite session and returning
   the connection to the pool.

9. Uvicorn sends HTTP 201 Created + JSON back across the network to the mobile app.
```

---

## 4. Deep-Dive: Why We Chose This Approach vs. Alternatives

### A. Web Framework: FastAPI vs. Flask vs. Django vs. Express (Node.js)

| Framework             | Concurrency Model              | Data Validation                                              | Documentation                            | Verdict for our project                                                                                                               |
| :-------------------- | :----------------------------- | :----------------------------------------------------------- | :--------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ |
| **FastAPI** (Chosen)  | **Native ASGI (Asynchronous)** | **Built-in (Pydantic v2)**                                   | **Auto-generated Swagger & ReDoc**       | ⭐️ **Best Choice**: Ultra-fast, type-safe, eliminates manual boilerplate, auto-generates live docs for mobile developers.             |
| **Flask**             | Synchronous WSGI               | Manual (must write `request.get_json()` & validation checks) | Third-party plugins required (Flasgger)  | Outdated for modern APIs; requires dozens of external packages to achieve what FastAPI has out of the box.                            |
| **Django**            | Heavy synchronous monolith     | Django Forms / DRF Serializers                               | Requires `drf-spectacular` or `drf-yasg` | Overkill for an API-first backend. Forces Django's built-in auth, template engine, and admin panels that our mobile app does not use. |
| **Express.js** (Node) | Single-threaded Event Loop     | Manual or external (Joi / Zod)                               | Manual (Swagger JSDoc)                   | Good performance, but lacks native Python data science/AI ecosystem integrations and Python's clean type system.                      |

#### Why FastAPI won:

1. **Developer Velocity**: Creating an endpoint automatically produces the data validator, the JSON serializer, and the interactive `/docs` documentation simultaneously.
2. **Type Safety**: Python type hints (`item_id: int`, `search: str | None = None`) prevent silent bugs.
3. **Speed**: Built on top of Starlette and Pydantic (core written in Rust), making it one of the fastest Python frameworks in existence.

---

### B. Database: SQLite vs. PostgreSQL vs. MongoDB (NoSQL)

| Database            | Architecture                | Setup Complexity                       | Concurrency                             | Why we chose it / When to upgrade                                                                                                                                                                    |
| :------------------ | :-------------------------- | :------------------------------------- | :-------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SQLite** (Chosen) | **Serverless, Single-File** | **Zero Setup (Built into Python)**     | Excellent for reads; single-writer lock | ⭐️ **Ideal for Local Dev & Learning**: All 540 items and orders are stored in `yummy.db` on your hard drive. No Docker, no daemon process, no cloud cost.                                            |
| **PostgreSQL**      | Client-Server RDBMS         | Requires server install or Docker      | Massive multi-user concurrency          | **The Production Target**: When shipping to AWS/GCP, we switch the connection URL in `database.py` to Postgres. Our SQLAlchemy code requires **zero rewrites**.                                      |
| **MongoDB** (NoSQL) | Document Store (BSON)       | Requires server install or Mongo Atlas | High read/write throughput              | **Poor fit for E-commerce/Food**: Food ordering requires strict relational integrity (orders must reference valid dish IDs and user IDs). MongoDB does not enforce relational foreign keys natively. |

---

### C. Data Access: SQLAlchemy ORM vs. Raw SQL

- **The Raw SQL Approach (`sqlite3` / `psycopg2`)**:
  ```python
  cursor.execute("SELECT id, name, price FROM menu_items WHERE id = " + user_input) # Vulnerable to SQL Injection!
  ```
  _Downsides_: Prone to SQL injection vulnerabilities, requires manual tuple-to-dictionary mapping, and ties your code to one specific database syntax.
- **The SQLAlchemy ORM Approach (Chosen)**:
  ```python
  item = db.query(models.DBMenuItem).filter(models.DBMenuItem.id == item_id).first()
  ```
  _Benefits_:
  - **SQL Injection Proof**: Parameterization is handled automatically.
  - **Database Agnostic**: The exact same query works whether SQLite, PostgreSQL, MySQL, or Oracle is running underneath.
  - **Relationship Management**: Accessing `order.item.name` automatically resolves the SQL `JOIN` without writing raw join clauses.

---

### D. Validation: Pydantic vs. Manual Parsing

- **Manual Validation (Old Way)**:
  ```python
  data = request.json
  if "name" not in data or len(data["name"]) < 2:
      return {"error": "Invalid name"}, 400
  if "price" not in data or data["price"] <= 0:
      return {"error": "Invalid price"}, 400
  ```
  _Downsides_: Fragile, repetitive, unmaintainable across 20+ endpoints.
- **Pydantic Schemas (Chosen)**:
  ```python
  class MenuItemCreate(BaseModel):
      name: str = Field(..., min_length=2, max_length=100)
      price: float = Field(..., gt=0)
  ```
  _Benefits_: Self-documenting code. Any payload violating these rules is rejected before it ever touches your database.

---

### E. Security: bcrypt Hashing vs. Plain/MD5/SHA

Why can't we store passwords in plain text or using MD5/SHA256?

1. **Plain Text**: If the database file is compromised or viewed in SQLite Viewer, every user's personal password is exposed.
2. **MD5 / SHA256**: Too fast. Attackers can compute billions of SHA256 hashes per second using GPUs and reverse-lookup passwords using precomputed **Rainbow Tables**.
3. **bcrypt (Chosen)**:
   - Uses an **adaptive, CPU-intensive key derivation algorithm**.
   - Generates a **cryptographic random salt** for every single password. Even if two users have the exact same password (`"Password123"`), their resulting hashes are completely different.
   - Resists brute-force and hardware acceleration attacks.

---

## 5. Codebase Organization & Separation of Concerns

Our project adheres to the **Single Responsibility Principle (SRP)**:

```
yummy-backend/
│
├── database.py              # Database engine, SessionLocal factory, and get_db()
├── models.py                # SQLAlchemy DB models (tables on disk)
├── schemas.py               # Pydantic schemas (HTTP validation & serialization)
├── main.py                  # API routes, middleware, and business logic
├── seed_indian_food.py      # Automated database seeder (540 items)
├── yummy.db                 # Persistent SQLite database storage file
├── requirements.txt         # Locked project dependencies
└── .venv/                   # Isolated virtual environment
```

### Why not put everything in `main.py`?

When backends grow to hundreds of routes:

- Putting database models and API routes together leads to circular import bugs.
- Separating `models.py` (database structure) from `schemas.py` (API contract) ensures you never leak sensitive database fields (like `hashed_password`) to the client.

---

## 6. Database Schema & Entity Relationships

The SQLite database (`yummy.db`) is structured into three relational tables:

```
 ┌─────────────────────────────────────────┐
 │               users                     │
 ├─────────────────────────────────────────┤
 │  id: Integer (PK, Indexed)              │
 │  full_name: String                      │
 │  email: String (Unique, Indexed)        │
 │  mobile: String (Unique, Indexed)       │
 │  hashed_password: String (bcrypt)       │
 │  dob: String (YYYY-MM-DD)               │
 └─────────────────────────────────────────┘

 ┌─────────────────────────────────────────┐
 │             menu_items                  │
 ├─────────────────────────────────────────┤
 │  id: Integer (PK, Indexed)              │◄────────┐
 │  name: String (Indexed)                 │         │
 │  description: String (Nullable)         │         │
 │  price: Float                           │         │ (1-to-Many)
 │  category: String (Indexed)             │         │
 │  image_url: String                      │         │ One dish can
 │  is_available: Boolean (Default: True)  │         │ appear in many
 └─────────────────────────────────────────┘         │ orders
                      ▲                              │
                      │                              │
 ┌────────────────────┴────────────────────┐         │
 │                orders                   │         │
 ├─────────────────────────────────────────┤         │
 │  id: Integer (PK, Indexed)              │         │
 │  customer_name: String                  │         │
 │  item_id: Integer (Foreign Key) ────────┴─────────┘
 │  quantity: Integer (Default: 1)
 │  total_price: Float
 │  status: String ("received", "preparing", "delivered")
 └─────────────────────────────────────────┘
```

---

## 7. Step-by-Step Guide: How to Start and Run the Project

### Phase 1: Environment Setup (One-time setup)

If setting up on a new machine:

```bash
# 1. Clone or open the folder
cd yummy-backend

# 2. Create the virtual environment
python -m venv .venv

# 3. Activate the environment:
# If using Git Bash:
source .venv/Scripts/activate

# If using PowerShell:
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt
```

---

### Phase 2: Seeding the Data (If starting with a blank database)

If `yummy.db` is deleted or you want to reset all 540 dishes:

```bash
python seed_indian_food.py
```

---

### Phase 3: Launching the Backend Server

To allow **both your computer and your mobile phone** on the local Wi-Fi to communicate with the server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Explanation of flags:

- `main:app`: Look in `main.py` for the variable named `app = FastAPI()`.
- `--reload`: Hot-reloading mode. Watches for code modifications and restarts instantly upon saving files.
- `--host 0.0.0.0`: **Binds to all network interfaces**. Without this, the server only listens to `127.0.0.1` and mobile phones cannot reach it.
- `--port 8000`: Port number the server accepts connections on.

---

## 8. Connecting to Mobile Applications (Android, iOS, Physical Devices)

When building client apps (Flutter, React Native, Swift, Kotlin), the client must make requests to the correct host address:

### Network Address Mapping:

| Mobile Environment              | API Base URL               | Why?                                                                                                                                                   |
| :------------------------------ | :------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Android Studio Emulator**     | `http://10.0.2.2:8000`     | The Android emulator runs in a virtual router. `10.0.2.2` is a special alias hardcoded by Google to route traffic back to your computer's `localhost`. |
| **iOS Simulator**               | `http://localhost:8000`    | The iOS simulator shares the Mac's network stack directly.                                                                                             |
| **Physical Phone (over Wi-Fi)** | `http://192.168.1.11:8000` | Your computer's local IP address on your Wi-Fi network. Both laptop and phone must be on the same Wi-Fi network.                                       |

### Why CORS is Enabled:

In `main.py`, we added:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Without this middleware, HTTP clients (especially web browsers and hybrid webviews) block requests with `CORS policy: No 'Access-Control-Allow-Origin' header is present`.

---

## 9. Troubleshooting & Common Pitfalls

### 1. `Cannot order: Dish with ID X does not exist`

- **Cause**: Trying to order a dish ID before the database is seeded.
- **Fix**: Run `python seed_indian_food.py` to populate all 540 items.

### 2. Mobile App Shows `Network Error` / `Connection Refused`

- **Check 1**: Did you run Uvicorn with `--host 0.0.0.0`? (If you ran default `uvicorn main:app`, it only binds to `127.0.0.1`).
- **Check 2**: Ensure your phone and your development machine are connected to the exact same Wi-Fi router.
- **Check 3**: On Windows, ensure Windows Firewall isn't blocking port 8000 on private networks.

### 3. PowerShell Script Disabled Error

- **Error**: `running scripts is disabled on this system`.
- **Fix**: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your PowerShell terminal, then activate.

---

## 10. Future Production Roadmap

When you are ready to deploy this backend to the cloud (AWS, Railway, Render, DigitalOcean):

1. **Database Migration to PostgreSQL**:
   - Change `SQLALCHEMY_DATABASE_URL = "sqlite:///./yummy.db"` in `database.py` to:
     `postgresql://user:password@host:5432/yummydb`.
2. **JWT Authentication**:
   - Issue signed JSON Web Tokens (JWT) on login so users pass `Authorization: Bearer <token>` for authenticated endpoints.
3. **Database Migrations with Alembic**:
   - Track database schema changes in version control without needing to drop/recreate tables.
4. **Cloud Image Hosting**:
   - Host dish photos on AWS S3 or Cloudinary with an image upload route (`POST /menu/upload-image`).
