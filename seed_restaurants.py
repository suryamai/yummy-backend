"""
Seed initial restaurants and marketing banners for YumQuick v3.
Links the 540 dishes to appropriate restaurants based on cuisine and category.
"""

from database import SessionLocal
import models

RESTAURANTS_SEED = [
    {
        "name": "Meghana Foods (Biryani & Andhra)",
        "cover_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&auto=format&fit=crop",
        "cuisines": "Biryani, Andhra, South Indian",
        "rating": 4.6,
        "rating_count": 1420,
        "lat": 12.9716,
        "lng": 77.5946,
        "open_time": "11:00 AM",
        "close_time": "11:30 PM",
        "min_order": 149.0,
        "delivery_radius_km": 15.0,
        "base_delivery_fee": 30.0,
        "is_open": True,
        "is_pure_veg": False,
        "categories": ["Biryani & Rice", "South Indian"]
    },
    {
        "name": "MTR 1924 (Mavalli Tiffin Room)",
        "cover_url": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=800&auto=format&fit=crop",
        "cuisines": "South Indian, Pure Veg, Breakfast",
        "rating": 4.8,
        "rating_count": 2500,
        "lat": 12.9550,
        "lng": 77.5860,
        "open_time": "06:30 AM",
        "close_time": "10:00 PM",
        "min_order": 99.0,
        "delivery_radius_km": 10.0,
        "base_delivery_fee": 20.0,
        "is_open": True,
        "is_pure_veg": True,
        "categories": ["South Indian", "Breads & Roti"]
    },
    {
        "name": "Punjab Grill & Tandoor",
        "cover_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=800&auto=format&fit=crop",
        "cuisines": "North Indian, Tandoor, Mughlai",
        "rating": 4.5,
        "rating_count": 890,
        "lat": 12.9780,
        "lng": 77.6400,
        "open_time": "12:00 PM",
        "close_time": "11:00 PM",
        "min_order": 199.0,
        "delivery_radius_km": 12.0,
        "base_delivery_fee": 35.0,
        "is_open": True,
        "is_pure_veg": False,
        "categories": ["North Indian", "Tandoor & Starters", "Breads & Roti"]
    },
    {
        "name": "Chowman (Indo-Chinese Delights)",
        "cover_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=800&auto=format&fit=crop",
        "cuisines": "Indo-Chinese, Noodles, Momos",
        "rating": 4.4,
        "rating_count": 650,
        "lat": 12.9600,
        "lng": 77.6000,
        "open_time": "11:30 AM",
        "close_time": "11:00 PM",
        "min_order": 120.0,
        "delivery_radius_km": 10.0,
        "base_delivery_fee": 25.0,
        "is_open": True,
        "is_pure_veg": False,
        "categories": ["Indo-Chinese"]
    },
    {
        "name": "Haldiram's Sweets & Chaat",
        "cover_url": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=800&auto=format&fit=crop",
        "cuisines": "Street Food, Chaat, Mithai, Sweets",
        "rating": 4.7,
        "rating_count": 3100,
        "lat": 12.9800,
        "lng": 77.5900,
        "open_time": "08:00 AM",
        "close_time": "10:30 PM",
        "min_order": 99.0,
        "delivery_radius_km": 15.0,
        "base_delivery_fee": 20.0,
        "is_open": True,
        "is_pure_veg": True,
        "categories": ["Street Food & Chaat", "Sweets & Desserts"]
    },
    {
        "name": "Chai Point & Desi Beverages",
        "cover_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=800&auto=format&fit=crop",
        "cuisines": "Chai, Filter Coffee, Lassi, Snacks",
        "rating": 4.5,
        "rating_count": 920,
        "lat": 12.9650,
        "lng": 77.6100,
        "open_time": "07:00 AM",
        "close_time": "11:00 PM",
        "min_order": 60.0,
        "delivery_radius_km": 12.0,
        "base_delivery_fee": 15.0,
        "is_open": True,
        "is_pure_veg": True,
        "categories": ["Beverages & Drinks", "Street Food & Chaat"]
    },
    {
        "name": "Udupi Sri Krishna Bhavan",
        "cover_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=800&auto=format&fit=crop",
        "cuisines": "South Indian, Thali, Pure Veg",
        "rating": 4.6,
        "rating_count": 1800,
        "lat": 12.9750,
        "lng": 77.5700,
        "open_time": "06:30 AM",
        "close_time": "10:30 PM",
        "min_order": 80.0,
        "delivery_radius_km": 10.0,
        "base_delivery_fee": 20.0,
        "is_open": True,
        "is_pure_veg": True,
        "categories": ["South Indian", "Breads & Roti"]
    },
    {
        "name": "Desi Rasoi (Regional Indian Flavors)",
        "cover_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=800&auto=format&fit=crop",
        "cuisines": "Regional Specials, Rajasthani, Bihari, Bengali",
        "rating": 4.5,
        "rating_count": 540,
        "lat": 12.9850,
        "lng": 77.6200,
        "open_time": "12:00 PM",
        "close_time": "11:00 PM",
        "min_order": 150.0,
        "delivery_radius_km": 14.0,
        "base_delivery_fee": 30.0,
        "is_open": True,
        "is_pure_veg": False,
        "categories": ["Regional Specials", "North Indian"]
    }
]

BANNERS_SEED = [
    {
        "title": "50% OFF Your First Feast",
        "subtitle": "Use code WELCOME50 on orders above ₹199",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&auto=format&fit=crop",
        "promo_code": "WELCOME50",
        "discount_percent": 50.0
    },
    {
        "title": "Flat ₹100 OFF on Biryanis",
        "subtitle": "Hot dum biryanis delivered in 30 mins",
        "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=800&auto=format&fit=crop",
        "promo_code": "BIRYANILOVER",
        "discount_percent": 25.0
    },
    {
        "title": "Chai & Street Food Combo",
        "subtitle": "Free delivery on all evening snack orders",
        "image_url": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=800&auto=format&fit=crop",
        "promo_code": "CHAI20",
        "discount_percent": 20.0
    }
]

def seed_restaurants_and_banners():
    session = SessionLocal()
    try:
        # 1. Seed Restaurants if empty
        if session.query(models.DBRestaurant).count() == 0:
            print("Seeding restaurants...")
            rest_objects = []
            for r in RESTAURANTS_SEED:
                rest_obj = models.DBRestaurant(
                    name=r["name"],
                    cover_url=r["cover_url"],
                    cuisines=r["cuisines"],
                    rating=r["rating"],
                    rating_count=r["rating_count"],
                    lat=r["lat"],
                    lng=r["lng"],
                    open_time=r["open_time"],
                    close_time=r["close_time"],
                    min_order=r["min_order"],
                    delivery_radius_km=r["delivery_radius_km"],
                    base_delivery_fee=r["base_delivery_fee"],
                    is_open=r["is_open"],
                    is_pure_veg=r["is_pure_veg"]
                )
                session.add(rest_obj)
            session.commit()
            print("Restaurants seeded successfully!")

        # 2. Link menu items to restaurants based on category
        all_restaurants = session.query(models.DBRestaurant).all()
        if all_restaurants:
            print("Linking 540 dishes to restaurants...")
            for idx, r_data in enumerate(RESTAURANTS_SEED):
                if idx < len(all_restaurants):
                    r_id = all_restaurants[idx].id
                    cats = r_data["categories"]
                    session.query(models.DBMenuItem).filter(
                        models.DBMenuItem.category.in_(cats),
                        models.DBMenuItem.restaurant_id == None
                    ).update({"restaurant_id": r_id}, synchronize_session=False)
            
            # Any remaining dishes without restaurant link to first restaurant
            first_id = all_restaurants[0].id
            session.query(models.DBMenuItem).filter(
                models.DBMenuItem.restaurant_id == None
            ).update({"restaurant_id": first_id}, synchronize_session=False)
            session.commit()
            print("Dishes linked to restaurants!")

        # 3. Seed Banners if empty
        if session.query(models.DBBanner).count() == 0:
            print("Seeding promo banners...")
            for b in BANNERS_SEED:
                banner_obj = models.DBBanner(
                    title=b["title"],
                    subtitle=b["subtitle"],
                    image_url=b["image_url"],
                    promo_code=b["promo_code"],
                    discount_percent=b["discount_percent"],
                    is_active=True
                )
                session.add(banner_obj)
            session.commit()
            print("Banners seeded successfully!")

    finally:
        session.close()

if __name__ == "__main__":
    seed_restaurants_and_banners()
