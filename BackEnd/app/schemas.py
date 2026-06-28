from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image: Optional[str] = None
    category: Optional[str] = None
    stock: int = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    image: Optional[str]
    category: Optional[str]
    stock: int

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]
    discount: float = 0.0
    total_price: float


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product_name: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    user_id: int
    client_name: str
    total_price: float
    discount: float
    status: str
    created_at: str
    items_count: int
    items: list[OrderItemResponse]


class OrderStatusUpdate(BaseModel):
    status: str


class ClientResponse(BaseModel):
    name: str
    email: str
    orders_count: int
    total_spent: float
    last_purchase: Optional[str] = None