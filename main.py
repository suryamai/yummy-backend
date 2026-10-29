from fastapi import FastAPI

# 1. Initialize the app instance
app = FastAPI(
    title = "Yummy Backend API",
    version = "1.0.0"
)

# 2. Define a root endpoint ( Health Check )
@app.get("/")
def home():
    return {
        "status" : "online",
        "message" : "Welcome to Yummy Backend!"
    }

#  3. Define a sample dynamic endpoint with a parameter
@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {
        "item_id": item_id,
        "name": f"Delicious Item #{item_id}"
    }