import datetime
import random
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

EMOJIS = ["👻", "🦇", "🕷️", "💀"]

def get_random_emoji():
    return random.choice(EMOJIS)

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    merchant = Column(String, nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    total = Column(Float, nullable=False)
    category = Column(String, nullable=False)  # Food, Shopping, Transport, Entertainment, Health, Utilities, Other
    items = Column(Text, default="[]")  # JSON string
    image_base64 = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    splits = relationship("Split", back_populates="receipt", cascade="all, delete-orphan")

class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    emoji = Column(String, default=get_random_emoji)

    splits = relationship("Split", back_populates="friend", cascade="all, delete-orphan")

class Split(Base):
    __tablename__ = "splits"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False)
    friend_id = Column(Integer, ForeignKey("friends.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    paid = Column(Boolean, default=False)
    split_type = Column(String, nullable=False)  # equal, custom, item
    you_owe = Column(Boolean, default=False)
    payment_proof = Column(Text, nullable=True)

    receipt = relationship("Receipt", back_populates="splits")
    friend = relationship("Friend", back_populates="splits")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, unique=True, index=True, nullable=False)  # YYYY-MM
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
