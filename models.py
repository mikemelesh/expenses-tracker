from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class Currency(str, enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    RUB = "RUB"
    BYN = "BYN"

class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_pwd = Column(String, nullable=False)

    expenses = relationship("ExpenseTable", back_populates="owner")

class CategoryTable(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String, default="💰")

    expenses = relationship("ExpenseTable", back_populates="category")

class ExpenseTable(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    currency = Column(SQLEnum(Currency), default=Currency.USD)

    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))

    owner = relationship("UserTable", back_populates="expenses")
    category = relationship("CategoryTable", back_populates="expenses")