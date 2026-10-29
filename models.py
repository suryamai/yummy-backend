from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class DBMenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)

    # 1-to-Many Relationship: One menu item can appear in many orders
    orders = relationship("DBOrder", back_populates="item")


class DBOrder(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="received")  # received -> preparing -> delivered

    # FOREIGN KEY: Links this order to a specific menu item id
    item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)

    # Allows accessing the dish directly (e.g. order.item.name)
    item = relationship("DBMenuItem", back_populates="orders")


class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    mobile = Column(String, unique=True, index=True, nullable=False)
    dob = Column(String, nullable=False)  # e.g. "2000-01-15"
