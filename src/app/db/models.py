from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.db.base import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ownership
    admin_user_id = Column(Integer, nullable=False) # Telegram User ID of the creator
    allowed_users = Column(JSON, default=list)      # List of allowed Telegram User IDs
    
    # Premium Status
    is_premium = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)
    
    # Relationships
    events = relationship("Event", back_populates="tenant", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    user_id = Column(Integer, nullable=False) # Who logged it
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    event_type = Column(String, nullable=False) # 'cacca', 'pipi', 'poppata', etc.
    details = Column(JSON, default=dict)        # Flexible payload (e.g. {side: 'L', duration: 10})
    
    # Relationships
    tenant = relationship("Tenant", back_populates="events")

class Baby(Base):
    __tablename__ = "babies"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, unique=True) # One baby per tenant for now
    
    name = Column(String, nullable=False)
    birth_date = Column(DateTime, nullable=True)
    weight_g = Column(Integer, nullable=True) # Grams
    height_cm = Column(Integer, nullable=True) # Centimeters
    
    # Relationships
    tenant = relationship("Tenant", back_populates="baby")

# Update Tenant to include baby relationship
Tenant.baby = relationship("Baby", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
