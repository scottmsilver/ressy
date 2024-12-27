from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Enum,
    Boolean, UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship, validates
from datetime import datetime, date
from enum import Enum as PyEnum
from database import Base, engine
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator, root_validator, ConfigDict, field_validator, model_validator

class BedType(PyEnum):
    SINGLE = "single"
    DOUBLE = "double"
    QUEEN = "queen"
    KING = "king"

class ReservationStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"

class BedSubType(PyEnum):
    STANDARD = "standard"
    SOFA = "sofa"
    BUNK = "bunk"
    ROLLAWAY = "rollaway"

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    buildings = relationship("Building", back_populates="property")

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    property = relationship("Property", back_populates="buildings")
    rooms = relationship("Room", back_populates="building")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    room_number = Column(String, nullable=False)
    building_id = Column(Integer, ForeignKey("buildings.id"))
    amenities = Column(JSON, default=list)
    
    building = relationship("Building", back_populates="rooms")
    beds = relationship("Bed", back_populates="room", cascade="all, delete")
    reservations = relationship("Reservation", back_populates="room", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('building_id', 'room_number', name='_building_room_number_uc'),
    )

    @property
    def capacity(self):
        return sum(bed.capacity for bed in self.beds)

class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    bed_type = Column(Enum(BedType))
    bed_subtype = Column(Enum(BedSubType))
    room = relationship("Room", back_populates="beds")

    @property
    def capacity(self):
        capacities = {
            BedType.SINGLE: 1,
            BedType.DOUBLE: 2,
            BedType.QUEEN: 2,
            BedType.KING: 2
        }
        return capacities[self.bed_type]

class Family(Base):
    __tablename__ = "families"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    primary_contact_id = Column(Integer, ForeignKey("guests.id", use_alter=True, name="fk_family_primary_contact"), nullable=True)
    guests = relationship("Guest", back_populates="family", 
                        foreign_keys="[Guest.family_id]",
                        primaryjoin="Family.id==Guest.family_id",
                        cascade="all, delete")
    primary_contact = relationship("Guest", 
                                foreign_keys=[primary_contact_id],
                                primaryjoin="Family.primary_contact_id==Guest.id",
                                post_update=True)

class Guest(Base):
    __tablename__ = "guests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    preferences = Column(JSON, default=dict)
    contact_emails = Column(JSON, default=list)
    family_id = Column(Integer, ForeignKey("families.id"))
    
    family = relationship("Family", back_populates="guests", 
                        foreign_keys=[family_id],
                        primaryjoin="Guest.family_id==Family.id")
    reservations = relationship("Reservation", back_populates="guest", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('email IS NOT NULL OR phone IS NOT NULL', name='check_contact_info'),
    )
    
    def __init__(self, **kwargs):
        if "contact_emails" not in kwargs:
            kwargs["contact_emails"] = []
        if "preferences" not in kwargs:
            kwargs["preferences"] = {}
        super().__init__(**kwargs)
    
    def add_contact_email(self, email: str):
        """Add a contact email to the guest's list"""
        if not self.contact_emails:
            self.contact_emails = []
        if email not in self.contact_emails:
            self.contact_emails = self.contact_emails + [email]
    
    def remove_contact_email(self, email: str):
        """Remove a contact email from the guest's list"""
        if not self.contact_emails:
            return
        if email in self.contact_emails:
            self.contact_emails = [e for e in self.contact_emails if e != email]

    @validates('email')
    def validate_email(self, key, email):
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email

    @validates('phone')
    def validate_phone(self, key, phone):
        if phone and not phone.replace('-', '').replace('+', '').isdigit():
            raise ValueError("Invalid phone format")
        return phone

class PropertyCreate(BaseModel):
    name: str
    address: str
    
    model_config = ConfigDict(from_attributes=True)

class PropertyResponse(BaseModel):
    id: int
    name: str
    address: str
    
    model_config = ConfigDict(from_attributes=True)

class BuildingCreate(BaseModel):
    name: str
    
    model_config = ConfigDict(from_attributes=True)

class BuildingResponse(BaseModel):
    id: int
    name: str
    property_id: int
    
    model_config = ConfigDict(from_attributes=True)

class RoomCreate(BaseModel):
    name: str
    room_number: str
    amenities: Optional[List[str]] = []
    
    model_config = ConfigDict(from_attributes=True)

class RoomResponse(BaseModel):
    id: int
    name: str
    room_number: str
    building_id: int
    amenities: List[str]
    capacity: int
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, room):
        return cls(
            id=room.id,
            name=room.name,
            room_number=room.room_number,
            building_id=room.building_id,
            amenities=room.amenities or [],
            capacity=room.capacity
        )

class GuestCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = {}
    contact_emails: Optional[List[str]] = []
    family_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def validate_contact_info(self) -> 'GuestCreate':
        if not self.email and not self.phone:
            raise ValueError("At least one contact method (email or phone) must be provided")
        return self

class GuestResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    preferences: Dict[str, Any]
    contact_emails: List[str]
    family_id: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)

class ReservationCreate(BaseModel):
    guest_id: int
    room_id: int
    start_date: date
    end_date: date
    num_guests: int
    special_requests: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def validate_dates(self) -> 'ReservationCreate':
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        return self

class ReservationResponse(BaseModel):
    id: int
    guest_id: int
    room_id: int
    start_date: date
    end_date: date
    num_guests: int
    special_requests: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, reservation):
        response = super().model_validate(reservation)
        response.start_date = reservation.start_date.date()
        response.end_date = reservation.end_date.date()
        return response

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    num_guests = Column(Integer, default=1)
    special_requests = Column(String, nullable=True)
    status = Column(String, default=ReservationStatus.CONFIRMED.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guest = relationship("Guest", back_populates="reservations")
    room = relationship("Room", back_populates="reservations")

class BedResponse(BaseModel):
    id: int
    bed_type: str
    bed_subtype: str
    room_id: int
    model_config = ConfigDict(from_attributes=True)
