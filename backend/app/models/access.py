from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class RolePermission(Base):
    __tablename__ = "role_permission_links"

    role_id = Column(Integer, ForeignKey("access_roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("access_permissions.id", ondelete="CASCADE"), primary_key=True)


class Role(Base):
    __tablename__ = "access_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary="role_permission_links", back_populates="roles")


class Permission(Base):
    __tablename__ = "access_permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=False, unique=True)
    description = Column(Text)

    roles = relationship("Role", secondary="role_permission_links", back_populates="permissions")


class User(Base):
    __tablename__ = "staff_users"
    __table_args__ = (UniqueConstraint("email", name="uq_staff_users_email"),)

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("access_roles.id"), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    role = relationship("Role", back_populates="users")
    created_orders = relationship("DeliveryOrder", back_populates="created_by")
    assigned_orders = relationship("OrderAssignment", back_populates="assigned_by")
    delivery_logs = relationship("DeliveryLog", back_populates="changed_by")
