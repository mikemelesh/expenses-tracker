from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime
from models import Currency

# --- CATEGORY SCHEMAS ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)
    icon: str = "💰"

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)
    email: EmailStr

class UserCreate(UserBase):
    """Used for Registration: Needs a password."""
    password: str = Field(..., min_length=8)

class User(UserBase):
    """Used for Response: Never return the password!"""
    model_config = ConfigDict(from_attributes=True)
    id: int

# --- EXPENSE SCHEMAS ---
class ExpenseBase(BaseModel):
    amount: float = Field(..., ge=1, le=999999999)
    description: Optional[str] = Field(None, max_length=999)
    currency: Currency = Currency.USD
    category_id: int

class ExpenseCreate(ExpenseBase):
    pass

class Expense(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    timestamp: datetime


