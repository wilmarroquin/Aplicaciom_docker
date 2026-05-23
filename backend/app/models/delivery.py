from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class Customer(Base):
    __tablename__ = "restaurant_customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False, index=True)
    phone = Column(String(30), nullable=False, index=True)
    email = Column(String(160), index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    addresses = relationship("DeliveryAddress", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("DeliveryOrder", back_populates="customer")


class DeliveryZone(Base):
    __tablename__ = "service_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    municipality = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    addresses = relationship("DeliveryAddress", back_populates="zone")


class PointOfInterest(Base):
    __tablename__ = "points_of_interest"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_poi_latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_poi_longitude_range"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(80), nullable=False, index=True)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DeliveryAddress(Base):
    __tablename__ = "customer_dropoff_points"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_dropoff_latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_dropoff_longitude_range"),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("restaurant_customers.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("service_areas.id"), nullable=False, index=True)
    street_address = Column(String(220), nullable=False)
    reference_note = Column(Text)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="addresses")
    zone = relationship("DeliveryZone", back_populates="addresses")
    orders = relationship("DeliveryOrder", back_populates="delivery_address")


class DeliveryStatus(Base):
    __tablename__ = "order_progress_states"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(40), nullable=False, unique=True)
    name = Column(String(80), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    orders = relationship("DeliveryOrder", back_populates="status")


class Courier(Base):
    __tablename__ = "delivery_couriers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False, index=True)
    phone = Column(String(30), nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    user_id = Column(Integer, ForeignKey("staff_users.id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assignments = relationship("OrderAssignment", back_populates="courier")


class DeliveryOrder(Base):
    __tablename__ = "restaurant_delivery_orders"
    __table_args__ = (CheckConstraint("order_total >= 0", name="ck_delivery_order_total_positive"),)

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("restaurant_customers.id"), nullable=False, index=True)
    delivery_address_id = Column(Integer, ForeignKey("customer_dropoff_points.id"), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey("order_progress_states.id"), nullable=False, index=True)
    order_total = Column(Numeric(10, 2), nullable=False)
    ordered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("staff_users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="orders")
    delivery_address = relationship("DeliveryAddress", back_populates="orders")
    status = relationship("DeliveryStatus", back_populates="orders")
    created_by = relationship("User", back_populates="created_orders")
    assignments = relationship("OrderAssignment", back_populates="order", cascade="all, delete-orphan")
    logs = relationship("DeliveryLog", back_populates="order", cascade="all, delete-orphan")


class OrderAssignment(Base):
    __tablename__ = "courier_dispatches"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("restaurant_delivery_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    courier_id = Column(Integer, ForeignKey("delivery_couriers.id"), nullable=False, index=True)
    assigned_by_user_id = Column(Integer, ForeignKey("staff_users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    order = relationship("DeliveryOrder", back_populates="assignments")
    courier = relationship("Courier", back_populates="assignments")
    assigned_by = relationship("User", back_populates="assigned_orders")


class DeliveryLog(Base):
    __tablename__ = "delivery_status_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("restaurant_delivery_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status_id = Column(Integer, ForeignKey("order_progress_states.id"), index=True)
    new_status_id = Column(Integer, ForeignKey("order_progress_states.id"), nullable=False, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("staff_users.id"), nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    order = relationship("DeliveryOrder", back_populates="logs")
    changed_by = relationship("User", back_populates="delivery_logs")
