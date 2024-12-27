from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, create_engine
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime, date, timedelta
from contextlib import asynccontextmanager

from database import SessionLocal, engine
from models import (
    PropertyCreate, PropertyResponse, BuildingCreate, BuildingResponse,
    RoomCreate, RoomResponse, BedResponse, GuestCreate, GuestResponse,
    ReservationCreate, ReservationResponse, Property, Building, Room, 
    Guest, Reservation, BedType, BedSubType
)
from property_manager import PropertyManager
from guest_manager import GuestManager
from reservation_manager import ReservationManager

from datetime import datetime, date, timedelta
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Property.metadata.create_all(bind=engine)
    yield
    # Clean up resources on shutdown if needed
    pass

app = FastAPI(lifespan=lifespan, title="Ressy API", description="Property Management System API")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request/response
class BedBase(BaseModel):
    bed_type: str
    bed_subtype: str
    model_config = ConfigDict(from_attributes=True)

class BedCreate(BedBase):
    pass

class BedResponse(BedBase):
    id: int
    capacity: int
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, bed):
        return cls(
            id=bed.id,
            bed_type=bed.bed_type.value,
            bed_subtype=bed.bed_subtype.value,
            capacity=bed.capacity
        )

class RoomBase(BaseModel):
    name: str
    room_number: str
    amenities: List[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: int
    building_id: int
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, room):
        return cls(
            id=room.id,
            name=room.name,
            room_number=room.room_number,
            building_id=room.building_id,
            amenities=room.amenities or []
        )

class RoomAmenitiesUpdate(BaseModel):
    amenities: List[str]
    model_config = ConfigDict(from_attributes=True)

class BuildingBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class BuildingCreate(BuildingBase):
    pass

class BuildingUpdate(BuildingBase):
    pass

class BuildingOut(BuildingBase):
    id: int
    name: str
    property_id: int
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, building):
        return cls(
            id=building.id,
            name=building.name,
            property_id=building.property_id
        )

class BuildingResponse(BuildingOut):
    rooms: List[RoomResponse]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, building):
        return cls(
            id=building.id,
            name=building.name,
            property_id=building.property_id,
            rooms=[RoomResponse.model_validate(room) for room in building.rooms]
        )

class PropertyBase(BaseModel):
    name: str
    address: str
    model_config = ConfigDict(from_attributes=True)

    @field_validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator('address')
    def validate_address(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Address cannot be empty")
        return v

class PropertyCreate(PropertyBase):
    pass

class PropertyResponse(PropertyBase):
    id: int
    buildings: List[BuildingResponse]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, property):
        return cls(
            id=property.id,
            name=property.name,
            address=property.address,
            buildings=[BuildingResponse.model_validate(b) for b in property.buildings]
        )

class GuestBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def validate_contact_info(cls, values):
        if not values.email and not values.phone:
            raise ValueError("At least one contact method (email or phone) must be provided")
        return values

    @field_validator('email')
    def validate_email(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Email cannot be empty string")
        return v

    @field_validator('phone')
    def validate_phone(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Phone cannot be empty string")
        return v

class GuestCreate(GuestBase):
    preferences: dict = Field(default_factory=dict)
    contact_emails: List[str] = Field(default_factory=list)
    family_id: Optional[int] = None
    override_duplicate: bool = False

class GuestResponse(GuestBase):
    id: int
    family_id: Optional[int] = None
    preferences: dict
    contact_emails: List[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, guest):
        contact_emails = guest.contact_emails or []
        if isinstance(contact_emails, str):
            contact_emails = [contact_emails]
        if guest.email and guest.email not in contact_emails:
            contact_emails.append(guest.email)

        return cls(
            id=guest.id,
            name=guest.name,
            email=guest.email,
            phone=guest.phone,
            family_id=guest.family_id,
            preferences=guest.preferences or {},
            contact_emails=contact_emails
        )

class FamilyBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class FamilyCreate(FamilyBase):
    primary_contact_id: Optional[int] = None

class FamilyResponse(FamilyBase):
    id: int
    primary_contact_id: Optional[int]
    guests: List[GuestResponse]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, family):
        return cls(
            id=family.id,
            name=family.name,
            primary_contact_id=family.primary_contact_id,
            guests=[GuestResponse.model_validate(g) for g in family.guests]
        )

class ReservationBase(BaseModel):
    guest_id: int
    room_id: int
    start_date: date
    end_date: date
    num_guests: int = 1
    special_requests: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ReservationCreate(ReservationBase):
    pass

class ReservationOut(BaseModel):
    id: int
    guest_id: int
    room_id: int
    start_date: date
    end_date: date
    num_guests: int
    special_requests: Optional[str]
    status: str
    model_config = ConfigDict(from_attributes=True)

class RoomAvailability(BaseModel):
    id: int
    room_number: str
    name: str
    model_config = ConfigDict(from_attributes=True)

class RoomConflict(BaseModel):
    start_date: date
    end_date: date
    guest_name: str
    model_config = ConfigDict(from_attributes=True)

class RoomAvailabilityCheck(BaseModel):
    available: bool
    conflicts: Optional[List[RoomConflict]]
    model_config = ConfigDict(from_attributes=True)

class PropertyAvailability(BaseModel):
    total_rooms: int
    available_rooms: List[RoomAvailability]
    occupied_rooms: Optional[List[dict]]
    model_config = ConfigDict(from_attributes=True)

class DailyReport(BaseModel):
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float
    check_ins: Optional[List[dict]]
    check_outs: Optional[List[dict]]
    staying: Optional[List[dict]]
    model_config = ConfigDict(from_attributes=True)

class BuildingReport(BaseModel):
    id: int
    name: str
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float
    revenue: float

class PropertyReport(BaseModel):
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float
    revenue: float
    avg_daily_rate: float
    buildings: List[BuildingReport]

class RevenueByDate(BaseModel):
    date: str
    revenue: float
    bookings: int

class PropertyRevenueReport(BaseModel):
    total_revenue: float
    total_bookings: int
    revenue_by_date: List[RevenueByDate]
    model_config = ConfigDict(from_attributes=True)

class OccupancyByDate(BaseModel):
    date: str
    occupied_rooms: int
    total_rooms: int
    occupancy_rate: float

class PropertyOccupancyReport(BaseModel):
    total_rooms: int
    avg_occupancy_rate: float
    occupancy_by_date: List[OccupancyByDate]
    model_config = ConfigDict(from_attributes=True)

class ForecastByDate(BaseModel):
    date: str
    predicted_occupancy: float
    predicted_revenue: float
    confidence: float

class PropertyForecastReport(BaseModel):
    total_predicted_revenue: float
    avg_predicted_occupancy: float
    forecast_by_date: List[ForecastByDate]
    model_config = ConfigDict(from_attributes=True)

# Initialize PropertyManager, GuestManager and ReservationManager
pm = PropertyManager()
gm = GuestManager()
rm = ReservationManager()

# Property endpoints
@app.post("/properties/", response_model=PropertyResponse)
def create_property(property: PropertyCreate, db: Session = Depends(get_db)):
    """Create a new property"""
    try:
        property_data = pm.create_property(db, property.name, property.address)
        return property_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/properties/", response_model=List[PropertyResponse])
def list_properties(name: Optional[str] = None, address: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List properties with optional filters"""
    if name or address:
        properties = pm.search_properties(session=db, name=name, address=address)
    else:
        properties = pm.list_properties(session=db, skip=skip, limit=limit)
    return [PropertyResponse.model_validate(p) for p in properties]

@app.get("/properties/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    """Get a property by ID"""
    property = pm.get_property(session=db, property_id=property_id)
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return PropertyResponse.model_validate(property)

@app.delete("/properties/{property_id}")
def delete_property(property_id: int, db: Session = Depends(get_db)):
    if not pm.delete_property(session=db, property_id=property_id):
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted"}

@app.post("/properties/generate", response_model=PropertyResponse)
def generate_random_property(db: Session = Depends(get_db)):
    db_property = pm.generate_random_property(session=db)
    return PropertyResponse.model_validate(db_property)

# Building endpoints
@app.post("/properties/{property_id}/buildings/", response_model=BuildingResponse)
def create_building(property_id: int, building: BuildingCreate, db: Session = Depends(get_db)):
    """Create a new building in a property"""
    try:
        db_building = pm.create_building(
            session=db,
            property_id=property_id,
            building_data={"name": building.name}
        )
        return BuildingResponse.model_validate(db_building)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/properties/{property_id}/buildings/", response_model=List[BuildingResponse])
def list_buildings(property_id: int, db: Session = Depends(get_db)):
    buildings = pm.list_buildings(session=db, property_id=property_id)
    return [BuildingResponse.model_validate(b) for b in buildings]

@app.delete("/buildings/{building_id}")
def delete_building(building_id: int, db: Session = Depends(get_db)):
    if not pm.delete_building(session=db, building_id=building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    return {"message": "Building deleted"}

@app.put("/buildings/{building_id}", response_model=BuildingResponse)
def update_building(building_id: int, building: BuildingUpdate, db: Session = Depends(get_db)):
    """Update a building"""
    try:
        db_building = pm.update_building(session=db, building_id=building_id, name=building.name)
        return BuildingResponse.model_validate(db_building)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Room endpoints
@app.post("/buildings/{building_id}/rooms/", response_model=RoomResponse)
def create_room(building_id: int, room: RoomCreate, session: Session = Depends(get_db)):
    """Create a new room in a building"""
    try:
        db_room = pm.create_room(
            session=session,
            building_id=building_id,
            name=room.name,
            room_number=room.room_number
        )
        return RoomResponse.model_validate(db_room)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Room number already exists in this building"
        )

@app.get("/buildings/{building_id}/rooms/", response_model=List[RoomResponse])
def list_rooms(building_id: int, db: Session = Depends(get_db)):
    rooms = pm.list_rooms(session=db, building_id=building_id)
    return [RoomResponse.model_validate(r) for r in rooms]

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    if not pm.delete_room(session=db, room_id=room_id):
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted"}

@app.put("/rooms/{room_id}/amenities", response_model=RoomResponse)
def update_room_amenities(room_id: int, amenities: RoomAmenitiesUpdate, db: Session = Depends(get_db)):
    """Update room amenities"""
    try:
        db_room = pm.update_room_amenities(session=db, room_id=room_id, amenities=amenities.amenities)
        return RoomResponse.model_validate(db_room)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/rooms/{room_id}/availability")
def check_room_availability(
    room_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    session: Session = Depends(get_db)
):
    """Check if a room is available for given dates"""
    try:
        # Validate dates
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        # Check if room exists
        room = session.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Check for conflicts
        conflicts = session.query(Reservation).filter(
            Reservation.room_id == room_id,
            Reservation.status == 'confirmed',
            or_(
                and_(
                    Reservation.start_date <= start_date,
                    Reservation.end_date > start_date
                ),
                and_(
                    Reservation.start_date < end_date,
                    Reservation.end_date >= end_date
                ),
                and_(
                    Reservation.start_date >= start_date,
                    Reservation.end_date <= end_date
                )
            )
        ).first()

        return {"available": not bool(conflicts)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Bed endpoints
@app.post("/rooms/{room_id}/beds/", response_model=BedResponse)
def create_bed(room_id: int, bed: BedCreate, db: Session = Depends(get_db)):
    try:
        db_bed = pm.add_bed(session=db, room_id=room_id, bed_type=bed.bed_type, bed_subtype=bed.bed_subtype)
        return BedResponse.model_validate(db_bed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/rooms/{room_id}/beds/", response_model=List[BedResponse])
def list_beds(room_id: int, db: Session = Depends(get_db)):
    """List all beds in a room"""
    beds = pm.list_beds(session=db, room_id=room_id)
    return [BedResponse.model_validate(bed) for bed in beds]

@app.delete("/beds/{bed_id}")
def delete_bed(bed_id: int, db: Session = Depends(get_db)):
    if not pm.delete_bed(session=db, bed_id=bed_id):
        raise HTTPException(status_code=404, detail="Bed not found")
    return {"message": "Bed deleted"}

# Guest endpoints
@app.post("/guests/", response_model=GuestResponse)
def create_guest(guest: GuestCreate, db: Session = Depends(get_db)):
    """Create a new guest"""
    try:
        guest_obj = gm.create_guest(db, guest, guest.override_duplicate)
        return GuestResponse.model_validate(guest_obj)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/guests/{guest_id}", response_model=GuestResponse)
def get_guest(guest_id: int, db: Session = Depends(get_db)):
    """Get a guest by ID"""
    guest = gm.get_guest(session=db, guest_id=guest_id)
    if guest is None:
        raise HTTPException(status_code=404, detail="Guest not found")
    return GuestResponse.model_validate(guest)

@app.get("/guests/", response_model=List[GuestResponse])
def search_guests(name: str = None, email: str = None, phone: str = None, db: Session = Depends(get_db)):
    """Search for guests by name, email, or phone"""
    try:
        if name:
            name = name.lower()
        guests = gm.find_guests(session=db, name=name, email=email, phone=phone)
        return [GuestResponse.model_validate(g) for g in guests]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/guests/{guest_id}/preferences", response_model=GuestResponse)
def update_guest_preferences(guest_id: int, preferences: dict, db: Session = Depends(get_db)):
    try:
        guest = gm.update_preferences(db, guest_id, preferences)
        return GuestResponse.model_validate(guest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/guests/merge", response_model=GuestResponse)
def merge_guests(merge_request: dict, db: Session = Depends(get_db)):
    try:
        # First get the guest to ensure it's in the session
        guest = gm.merge_guests(db, merge_request["primary_guest_id"], merge_request["secondary_guest_id"])
        # Refresh to get the latest state
        db.refresh(guest)
        print(f"Debug - Guest contact_emails after merge: {guest.contact_emails}")
        # Convert to response model and ensure contact_emails are included
        response = GuestResponse(
            id=guest.id,
            name=guest.name,
            email=guest.email,
            phone=guest.phone,
            family_id=guest.family_id,
            preferences=guest.preferences,
            contact_emails=guest.contact_emails if guest.contact_emails else []
        )
        print(f"Debug - Response contact_emails: {response.contact_emails}")
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/guests/{guest_id}/contact-emails", response_model=GuestResponse)
def add_contact_email(guest_id: int, email_data: dict, db: Session = Depends(get_db)):
    """Add a contact email to a guest"""
    guest = gm.get_guest(db, guest_id)
    if guest is None:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    email = email_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    if not guest.contact_emails:
        guest.contact_emails = []
    
    if email not in guest.contact_emails:
        guest.contact_emails.append(email)
        db.commit()
        db.refresh(guest)
    
    return GuestResponse.model_validate(guest)

# Family endpoints
@app.post("/families/", response_model=FamilyResponse)
def create_family(family: FamilyCreate, db: Session = Depends(get_db)):
    """Create a new family"""
    try:
        db_family = gm.create_family(
            session=db,
            name=family.name,
            primary_contact_id=family.primary_contact_id
        )
        db.refresh(db_family)  # Refresh to load relationships
        return FamilyResponse.model_validate(db_family)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/families/{family_id}/members/{guest_id}", response_model=GuestResponse)
def add_family_member(family_id: int, guest_id: int, db: Session = Depends(get_db)):
    try:
        guest = gm.add_family_member(session=db, family_id=family_id, guest_id=guest_id)
        return GuestResponse.model_validate(guest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/families/{family_id}/primary-contact/{guest_id}", response_model=FamilyResponse)
def set_primary_contact(family_id: int, guest_id: int, db: Session = Depends(get_db)):
    try:
        family = gm.set_primary_contact(session=db, family_id=family_id, guest_id=guest_id)
        return FamilyResponse.model_validate(family)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/families/{family_id}/members", response_model=List[GuestResponse])
def get_family_members(family_id: int, db: Session = Depends(get_db)):
    try:
        guests = gm.get_family_members(session=db, family_id=family_id)
        return [GuestResponse.model_validate(g) for g in guests]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/guests/{guest_id}/reservations", response_model=List[ReservationOut])
def get_guest_reservations(
    guest_id: int,
    include_cancelled: bool = False,
    db: Session = Depends(get_db)
) -> List[ReservationOut]:
    """Get all reservations for a guest"""
    guest = db.get(Guest, guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    query = db.query(Reservation).filter(Reservation.guest_id == guest_id)
    if not include_cancelled:
        query = query.filter(Reservation.status != ReservationStatus.CANCELLED.value)

    reservations = query.order_by(Reservation.start_date.desc()).all()
    return [
        {
            **r.__dict__,
            'guest_name': r.guest.name,
            'room_name': f"Room {r.room.room_number} - {r.room.name}"
        } for r in reservations
    ]

# Reservation endpoints
@app.post("/reservations/", response_model=ReservationOut)
def create_reservation(
    reservation: ReservationCreate,
    session: Session = Depends(get_db)
):
    """Create a new reservation"""
    try:
        # Validate dates
        if reservation.start_date >= reservation.end_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        # Check if room exists
        room = session.query(Room).filter(Room.id == reservation.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Check if guest exists
        guest = session.query(Guest).filter(Guest.id == reservation.guest_id).first()
        if not guest:
            raise HTTPException(status_code=404, detail="Guest not found")

        # Check for conflicts
        conflicts = session.query(Reservation).filter(
            Reservation.room_id == reservation.room_id,
            Reservation.status == 'confirmed',
            or_(
                and_(
                    Reservation.start_date <= reservation.start_date,
                    Reservation.end_date > reservation.start_date
                ),
                and_(
                    Reservation.start_date < reservation.end_date,
                    Reservation.end_date >= reservation.end_date
                ),
                and_(
                    Reservation.start_date >= reservation.start_date,
                    Reservation.end_date <= reservation.end_date
                )
            )
        ).first()

        if conflicts:
            raise HTTPException(
                status_code=400,
                detail="Room is not available for the selected dates"
            )

        # Create reservation
        db_reservation = Reservation(
            guest_id=reservation.guest_id,
            room_id=reservation.room_id,
            start_date=reservation.start_date,
            end_date=reservation.end_date,
            num_guests=reservation.num_guests,
            special_requests=reservation.special_requests,
            status='confirmed'
        )
        session.add(db_reservation)
        session.commit()
        session.refresh(db_reservation)
        return db_reservation

    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Invalid reservation data")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/reservations/{reservation_id}", response_model=ReservationOut)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Get a reservation by ID"""
    try:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return {
            **reservation.__dict__,
            'guest_name': reservation.guest.name,
            'room_name': f"Room {reservation.room.room_number} - {reservation.room.name}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Cancel a reservation"""
    try:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        if reservation.status == 'cancelled':
            raise HTTPException(status_code=400, detail="Reservation is already cancelled")
        
        reservation.status = 'cancelled'
        db.commit()
        return {"message": "Reservation cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/rooms/{room_id}/availability", response_model=RoomAvailabilityCheck)
def check_room_availability(
    room_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Check room availability for a date range"""
    try:
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        conflicts = db.query(Reservation).filter(
            Reservation.room_id == room_id,
            Reservation.status == 'confirmed',
            or_(
                and_(
                    Reservation.start_date <= start_date,
                    Reservation.end_date > start_date
                ),
                and_(
                    Reservation.start_date < end_date,
                    Reservation.end_date >= end_date
                ),
                and_(
                    Reservation.start_date >= start_date,
                    Reservation.end_date <= end_date
                )
            )
        ).all()
        
        if not conflicts:
            return {"available": True, "conflicts": None}
        
        return {
            "available": False,
            "conflicts": [
                {
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                    "guest_name": c.guest.name
                } for c in conflicts
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/properties/{property_id}/availability", response_model=PropertyAvailability)
def get_property_availability(
    property_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Get property availability for a date range"""
    try:
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        property = db.query(Property).filter(Property.id == property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Get all rooms in the property
        rooms = []
        for building in property.buildings:
            rooms.extend(building.rooms)
        
        if not rooms:
            return {
                "total_rooms": 0,
                "available_rooms": [],
                "occupied_rooms": []
            }
        
        # Check each room's availability
        available_rooms = []
        occupied_rooms = []
        
        for room in rooms:
            conflicts = db.query(Reservation).filter(
                Reservation.room_id == room.id,
                Reservation.status == 'confirmed',
                or_(
                    and_(
                        Reservation.start_date <= start_date,
                        Reservation.end_date > start_date
                    ),
                    and_(
                        Reservation.start_date < end_date,
                        Reservation.end_date >= end_date
                    ),
                    and_(
                        Reservation.start_date >= start_date,
                        Reservation.end_date <= end_date
                    )
                )
            ).all()
            
            if conflicts:
                occupied_rooms.append({
                    "id": room.id,
                    "room_number": room.room_number,
                    "name": room.name,
                    "reservations": [
                        {
                            "start_date": r.start_date,
                            "end_date": r.end_date,
                            "guest_name": r.guest.name
                        } for r in conflicts
                    ]
                })
            else:
                available_rooms.append({
                    "id": room.id,
                    "room_number": room.room_number,
                    "name": room.name
                })
        
        return {
            "total_rooms": len(rooms),
            "available_rooms": available_rooms,
            "occupied_rooms": occupied_rooms
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/reports/daily/{date}", response_model=DailyReport)
def get_daily_report(date: date, db: Session = Depends(get_db)):
    """Get daily occupancy report"""
    try:
        # Get all rooms
        total_rooms = db.query(Room).count()
        
        # Get reservations for the day
        reservations = db.query(Reservation).filter(
            Reservation.status == 'confirmed',
            Reservation.start_date <= date,
            Reservation.end_date > date
        ).all()
        
        occupied_rooms = len(reservations)
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        # Get check-ins and check-outs
        check_ins = []
        check_outs = []
        staying = []
        
        for res in reservations:
            room = res.room
            guest = res.guest
            res_info = {
                "reservation_id": res.id,
                "room_number": room.room_number,
                "guest_name": guest.name
            }
            
            if res.start_date.date() == date:
                check_ins.append(res_info)
            if res.end_date.date() == date + timedelta(days=1):
                check_outs.append(res_info)
            
            staying.append({
                **res_info,
                "end_date": res.end_date
            })
        
        return {
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "occupancy_rate": occupancy_rate,
            "check_ins": check_ins,
            "check_outs": check_outs,
            "staying": staying
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/properties/{property_id}/reports/summary", response_model=PropertyReport)
def get_property_report(
    property_id: int,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get a comprehensive property report"""
    try:
        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD")

        if start > end:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        print(f"DEBUG: Starting property report for property {property_id}")
        print(f"DEBUG: Date range: {start} to {end}")
        
        # Get all rooms in one query with their buildings
        print("DEBUG: Querying rooms and buildings...")
        rooms_query = (
            db.query(Room)
            .join(Building)
            .filter(Building.property_id == property_id)
            .with_entities(
                Room.id,
                Room.name,
                Building.id.label('building_id'),
                Building.name.label('building_name')
            )
        )
        print(f"DEBUG: SQL Query: {str(rooms_query)}")
        rooms = rooms_query.all()
        print(f"DEBUG: Found {len(rooms)} rooms")
        
        if not rooms:
            print("DEBUG: No rooms found, returning empty report")
            return {
                "total_rooms": 0,
                "occupied_rooms": 0,
                "occupancy_rate": 0,
                "revenue": 0,
                "avg_daily_rate": 0,
                "buildings": []
            }

        # Initialize counters
        total_rooms = len(rooms)
        room_ids = [room.id for room in rooms]
        buildings_map = {}
        
        print("DEBUG: Initializing building data...")
        # Initialize building data
        for room in rooms:
            if room.building_id not in buildings_map:
                buildings_map[room.building_id] = {
                    "id": room.building_id,
                    "name": room.building_name,
                    "total_rooms": 0,
                    "occupied_rooms": 0,
                    "revenue": 0
                }
            buildings_map[room.building_id]["total_rooms"] += 1
        print(f"DEBUG: Initialized {len(buildings_map)} buildings")

        # Get all reservations for these rooms in one query
        print("DEBUG: Querying reservations...")
        reservations_query = (
            db.query(Reservation)
            .filter(
                Reservation.room_id.in_(room_ids),
                Reservation.status == 'confirmed',
                Reservation.start_date <= end,
                Reservation.end_date > start
            )
            .with_entities(
                Reservation.room_id,
                Reservation.start_date,
                Reservation.end_date
            )
        )
        print(f"DEBUG: SQL Query: {str(reservations_query)}")
        reservations = reservations_query.all()
        print(f"DEBUG: Found {len(reservations)} reservations")

        # Process reservations
        occupied_rooms = set()
        total_revenue = 0
        
        print("DEBUG: Processing reservations...")
        for res in reservations:
            room_id = res.room_id
            if room_id not in occupied_rooms:
                # Find building for this room
                for room in rooms:
                    if room.id == room_id:
                        buildings_map[room.building_id]["occupied_rooms"] += 1
                        break
                occupied_rooms.add(room_id)
            
            # Calculate revenue
            res_start = max(res.start_date, start)
            res_end = min(res.end_date, end)
            nights = (res_end - res_start).days
            
            # Assuming a base rate of $100 per night
            room_revenue = nights * 100
            total_revenue += room_revenue
            
            # Update building revenue
            for room in rooms:
                if room.id == room_id:
                    buildings_map[room.building_id]["revenue"] += room_revenue
                    break
        print(f"DEBUG: Processed all reservations. Found {len(occupied_rooms)} occupied rooms")

        # Calculate metrics
        print("DEBUG: Calculating final metrics...")
        occupied_room_count = len(occupied_rooms)
        days_in_range = (end - start).days + 1  # Include both start and end dates
        occupancy_rate = (occupied_room_count / total_rooms * 100) if total_rooms > 0 else 0
        avg_daily_rate = (total_revenue / occupied_room_count / days_in_range) if occupied_room_count > 0 and days_in_range > 0 else 0

        # Calculate building occupancy rates
        buildings_data = []
        for building_data in buildings_map.values():
            if building_data["total_rooms"] > 0:
                building_data["occupancy_rate"] = (building_data["occupied_rooms"] / building_data["total_rooms"] * 100)
            else:
                building_data["occupancy_rate"] = 0
            buildings_data.append(building_data)

        print("DEBUG: Returning final report")
        return {
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_room_count,
            "occupancy_rate": occupancy_rate,
            "revenue": total_revenue,
            "avg_daily_rate": avg_daily_rate,
            "buildings": [BuildingReport(**b) for b in buildings_data]
        }
    except Exception as e:
        print(f"DEBUG: Error occurred: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/properties/{property_id}/reports/revenue", response_model=PropertyRevenueReport)
def get_property_revenue_report(
    property_id: int,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get a detailed revenue report for the property"""
    try:
        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD")

        if start > end:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        print(f"DEBUG: Starting revenue report for property {property_id}")
        print(f"DEBUG: Date range: {start} to {end}")

        # Get all rooms with their buildings in one query
        rooms = (
            db.query(Room)
            .join(Building)
            .filter(Building.property_id == property_id)
            .with_entities(
                Room.id,
                Room.name,
                Building.id.label('building_id'),
                Building.name.label('building_name')
            )
            .all()
        )

        if not rooms:
            return PropertyRevenueReport(
                total_revenue=0,
                total_bookings=0,
                revenue_by_date=[]
            )

        # Initialize counters
        total_revenue = 0
        total_bookings = 0
        revenue_by_date_map = {}

        # Get room IDs
        room_ids = [room.id for room in rooms]

        # Get all reservations in one query
        reservations = (
            db.query(Reservation)
            .filter(
                Reservation.room_id.in_(room_ids),
                Reservation.status == 'confirmed',
                Reservation.start_date <= end,
                Reservation.end_date > start
            )
            .all()
        )

        # Process reservations
        for res in reservations:
            # Calculate the stay duration within our date range
            res_start = max(res.start_date, start)
            res_end = min(res.end_date, end)
            nights = (res_end - res_start).days
            
            # Calculate revenue (assuming $100 per night)
            room_revenue = nights * 100
            total_revenue += room_revenue
            total_bookings += 1
            
            # Distribute revenue across dates
            daily_revenue = room_revenue / nights if nights > 0 else 0
            current_date = res_start
            while current_date < res_end:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str not in revenue_by_date_map:
                    revenue_by_date_map[date_str] = {"revenue": 0, "bookings": 0}
                revenue_by_date_map[date_str]["revenue"] += daily_revenue
                revenue_by_date_map[date_str]["bookings"] += 1
                current_date += timedelta(days=1)

        # Convert the map to a list of RevenueByDate objects
        revenue_by_date = [
            RevenueByDate(
                date=date,
                revenue=data["revenue"],
                bookings=data["bookings"]
            )
            for date, data in sorted(revenue_by_date_map.items())
        ]

        return PropertyRevenueReport(
            total_revenue=total_revenue,
            total_bookings=total_bookings,
            revenue_by_date=revenue_by_date
        )

    except Exception as e:
        print(f"DEBUG: Error in revenue report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/properties/{property_id}/reports/occupancy", response_model=PropertyOccupancyReport)
def get_property_occupancy_report(
    property_id: int,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get a detailed occupancy report for the property"""
    try:
        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD")

        if start > end:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        # Get all rooms with their buildings in one query
        rooms = (
            db.query(Room)
            .join(Building)
            .filter(Building.property_id == property_id)
            .with_entities(
                Room.id,
                Room.name,
                Building.id.label('building_id'),
                Building.name.label('building_name')
            )
            .all()
        )

        if not rooms:
            return {
                "total_rooms": 0,
                "avg_occupancy_rate": 0,
                "occupancy_by_date": []
            }

        # Initialize counters
        total_rooms = len(rooms)
        room_ids = [room.id for room in rooms]
        occupancy_data = []

        # Get all occupied rooms in one query
        occupied_rooms = (
            db.query(func.date(Reservation.start_date).label('date'))
            .distinct()
            .filter(
                Reservation.room_id.in_(room_ids),
                Reservation.status == 'confirmed',
                Reservation.start_date <= end,
                Reservation.end_date > start
            )
            .group_by('date')
            .all()
        )

        # Calculate occupancy rate for each date
        current_date = start
        while current_date <= end:
            occupied_count = (
                db.query(Reservation.room_id)
                .distinct()
                .filter(
                    Reservation.room_id.in_(room_ids),
                    Reservation.status == 'confirmed',
                    Reservation.start_date <= current_date,
                    Reservation.end_date > current_date
                )
                .count()
            )
            occupancy_rate = (occupied_count / total_rooms * 100) if total_rooms > 0 else 0
            occupancy_data.append((current_date.strftime("%Y-%m-%d"), occupied_count, occupancy_rate))
            current_date += timedelta(days=1)

        # Calculate average occupancy rate
        avg_occupancy_rate = sum(rate for _, _, rate in occupancy_data) / len(occupancy_data) if occupancy_data else 0

        return PropertyOccupancyReport(
            total_rooms=total_rooms,
            avg_occupancy_rate=avg_occupancy_rate,
            occupancy_by_date=[
                OccupancyByDate(
                    date=date,
                    occupied_rooms=occ,
                    total_rooms=total_rooms,
                    occupancy_rate=rate
                ) for date, occ, rate in occupancy_data
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/properties/{property_id}/reports/forecast", response_model=PropertyForecastReport)
def get_property_forecast_report(
    property_id: int,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get a forecast report for the property"""
    try:
        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD")

        if start > end:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        # Get all rooms with their buildings in one query
        rooms = (
            db.query(Room)
            .join(Building)
            .filter(Building.property_id == property_id)
            .with_entities(
                Room.id,
                Room.name,
                Building.id.label('building_id'),
                Building.name.label('building_name')
            )
            .all()
        )

        if not rooms:
            return {
                "total_predicted_revenue": 0,
                "avg_predicted_occupancy": 0,
                "forecast_by_date": []
            }

        # Initialize counters
        total_rooms = len(rooms)
        room_ids = [room.id for room in rooms]
        forecast_data = []

        # Get all occupied rooms in one query
        occupied_rooms = (
            db.query(func.date(Reservation.start_date).label('date'))
            .distinct()
            .filter(
                Reservation.room_id.in_(room_ids),
                Reservation.status == 'confirmed',
                Reservation.start_date <= end,
                Reservation.end_date > start
            )
            .group_by('date')
            .all()
        )

        # Calculate occupancy rate for each date
        current_date = start
        while current_date <= end:
            occupied_count = (
                db.query(Reservation.room_id)
                .distinct()
                .filter(
                    Reservation.room_id.in_(room_ids),
                    Reservation.status == 'confirmed',
                    Reservation.start_date <= current_date,
                    Reservation.end_date > current_date
                )
                .count()
            )
            occupancy_rate = (occupied_count / total_rooms * 100) if total_rooms > 0 else 0
            revenue = occupied_count * 100
            confidence = 0.8  # Assuming 80% confidence for now
            forecast_data.append((current_date.strftime("%Y-%m-%d"), occupancy_rate, revenue, confidence))
            current_date += timedelta(days=1)

        # Calculate average occupancy rate
        avg_occupancy_rate = sum(rate for _, rate, _, _ in forecast_data) / len(forecast_data) if forecast_data else 0
        total_predicted_revenue = sum(revenue for _, _, revenue, _ in forecast_data)

        return {
            "total_predicted_revenue": total_predicted_revenue,
            "avg_predicted_occupancy": avg_occupancy_rate,
            "forecast_by_date": [ForecastByDate(date=date, predicted_occupancy=occ, predicted_revenue=rev, confidence=conf) for date, occ, rev, conf in forecast_data]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
