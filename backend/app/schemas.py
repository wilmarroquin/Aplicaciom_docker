from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CustomerCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=7, max_length=30)
    email: Optional[EmailStr] = None
    notes: Optional[str] = None


class CustomerRead(CustomerCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ZoneRead(BaseModel):
    id: int
    name: str
    municipality: str
    department: str
    is_active: bool

    model_config = {"from_attributes": True}


class AddressCreate(BaseModel):
    customer_id: int
    zone_id: int
    street_address: str = Field(..., min_length=5, max_length=220)
    reference_note: Optional[str] = None
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    is_default: bool = False


class AddressRead(AddressCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PointOfInterestCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(..., min_length=5)
    category: str = Field(..., min_length=2, max_length=80)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)


class PointOfInterestRead(PointOfInterestCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CourierCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=7, max_length=30)
    is_available: bool = True


class CourierRead(CourierCreate):
    id: int

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_id: int
    delivery_address_id: int
    order_total: Decimal = Field(..., ge=0)


class OrderStatusUpdate(BaseModel):
    status_code: str
    comment: Optional[str] = None


class AssignmentCreate(BaseModel):
    courier_id: int


class OrderRead(BaseModel):
    id: int
    customer_id: int
    delivery_address_id: int
    status_id: int
    order_total: Decimal
    ordered_at: datetime

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str


class DeliveryReportItem(BaseModel):
    order_id: int
    customer_name: str
    courier_name: Optional[str]
    status: str
    zone: str
    order_total: Decimal
    ordered_at: datetime
