from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import (
    Property, Building, Room, Bed, BedType, BedSubType,
    PropertyCreate, BuildingCreate, RoomCreate
)
import random
from typing import Optional, List, Dict, Union

class PropertyManager:
    def create_property(self, session: Session, name: str, address: str) -> Property:
        """Create a new property"""
        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Property name cannot be empty")
        if not address or not address.strip():
            raise ValueError("Property address cannot be empty")

        # Create property
        property = Property(name=name.strip(), address=address.strip())
        session.add(property)
        session.commit()
        session.refresh(property)
        return property

    def list_properties(self, session: Session, name: Optional[str] = None, address: Optional[str] = None,
                       skip: int = 0, limit: int = 100) -> List[Property]:
        """List properties with optional filters"""
        query = session.query(Property)
        if name:
            query = query.filter(Property.name.ilike(f"%{name}%"))
        if address:
            query = query.filter(Property.address.ilike(f"%{address}%"))
        return query.offset(skip).limit(limit).all()

    def get_property(self, session: Session, property_id: int) -> Optional[Property]:
        """Get a property by ID"""
        return session.get(Property, property_id)

    def create_building(self, session: Session, property_id: int, building_data: dict) -> Building:
        """Create a new building in a property"""
        # Validate property exists
        property = session.get(Property, property_id)
        if not property:
            raise ValueError("Property not found")

        # Create building
        building = Building(
            name=building_data["name"],
            property_id=property_id
        )
        session.add(building)
        session.commit()
        session.refresh(building)
        return building

    def create_room(self, session: Session, building_id: int, name: str, room_number: str) -> Room:
        """Create a new room in a building"""
        # Validate building exists
        building = session.get(Building, building_id)
        if not building:
            raise ValueError("Building not found")

        # Create room
        room = Room(
            name=name,
            room_number=room_number,
            building_id=building_id,
            amenities=[]
        )
        session.add(room)
        session.commit()
        session.refresh(room)
        return room

    def add_bed(self, session: Session, room_id: int, bed_type: Union[str, BedType], bed_subtype: Union[str, BedSubType]) -> Bed:
        """Add a bed to a room"""
        # Validate room exists
        room = session.get(Room, room_id)
        if not room:
            raise ValueError("Room not found")

        # Convert string to enum if needed
        if isinstance(bed_type, str):
            bed_type = BedType[bed_type.upper()]
        if isinstance(bed_subtype, str):
            bed_subtype = BedSubType[bed_subtype.upper()]

        # Create bed
        bed = Bed(
            room_id=room_id,
            bed_type=bed_type,
            bed_subtype=bed_subtype
        )
        session.add(bed)
        session.commit()
        session.refresh(bed)
        return bed

    def delete_property(self, session: Session, property_id: int) -> bool:
        """Delete a property and all its related data"""
        property = session.get(Property, property_id)
        if not property:
            return False
            
        # Delete all buildings and their related data
        for building in property.buildings:
            # Delete all rooms in the building
            for room in building.rooms:
                # Delete all beds in the room
                for bed in room.beds:
                    session.delete(bed)
                # Delete all reservations for this room
                for reservation in room.reservations:
                    session.delete(reservation)
                session.delete(room)
            session.delete(building)
            
        session.delete(property)
        session.commit()
        return True

    def generate_random_property(self, session: Session):
        """Generate a random property with buildings and rooms"""
        # Lists for random names
        property_adjectives = ["Sunny", "Ocean", "Mountain", "Forest", "Lake", "River", "Valley", "Coastal"]
        property_nouns = ["Vista", "Retreat", "Lodge", "Resort", "Haven", "Escape", "Sanctuary", "Paradise"]
        building_types = ["Tower", "Wing", "House", "Villa", "Block", "Lodge", "Residence"]
        room_adjectives = ["Deluxe", "Premium", "Standard", "Executive", "Luxury", "Classic", "Superior"]
        room_types = ["Suite", "Room", "Studio", "Apartment"]
        room_purposes = ["Family", "Standard", "Dorm Style", "Youth Hostel", "Group"]

        # Generate property
        property_name = f"{random.choice(property_adjectives)} {random.choice(property_nouns)}"
        addresses = [
            "123 Oceanfront Drive, Seaside, CA",
            "456 Mountain View Road, Highland, CO",
            "789 Forest Lane, Woodland, OR",
            "321 Lakeside Avenue, Waterfront, WA",
            "654 Valley Way, Greendale, VT"
        ]
        property = self.create_property(session, name=property_name, address=random.choice(addresses))

        # Generate two buildings
        building_counts = [random.randint(4, 6), random.randint(2, 4)]  # 4-6 rooms in first, 2-4 in second
        for i in range(2):
            building_name = f"{random.choice(building_types)} {chr(65 + i)}"  # A, B, etc.
            building = self.create_building(session, property.id, {"name": building_name})
            
            # Generate rooms for this building
            for j in range(building_counts[i]):
                room_purpose = random.choice(room_purposes)
                room_name = f"{random.choice(room_adjectives)} {room_purpose} {random.choice(room_types)}"
                room_number = f"{i+1}{str(j+1).zfill(2)}"  # 101, 102, etc.
                room = self.create_room(session, building.id, room_name, room_number)
                
                # Determine room style
                room_style = random.choice([
                    "standard",    # Regular beds only
                    "mixed",       # Mix of regular and bunk beds
                    "bunk_only",   # All bunk beds
                    "family"       # Mix of large beds and bunks
                ])

                if room_style == "standard":
                    # 1-2 regular beds
                    num_beds = random.randint(1, 2)
                    for _ in range(num_beds):
                        bed_type = random.choice([BedType.QUEEN, BedType.KING])
                        self.add_bed(session, room.id, bed_type.name, BedSubType.REGULAR.name)

                elif room_style == "mixed":
                    # One regular bed and one bunk set
                    bed_type = random.choice([BedType.QUEEN, BedType.KING])
                    self.add_bed(session, room.id, bed_type.name, BedSubType.REGULAR.name)
                    self.add_bed(session, room.id, BedType.TWIN.name, BedSubType.UPPER.name)
                    self.add_bed(session, room.id, BedType.TWIN.name, BedSubType.LOWER.name)

                elif room_style == "bunk_only":
                    # 2-3 sets of bunk beds
                    num_bunks = random.randint(2, 3)
                    for _ in range(num_bunks):
                        self.add_bed(session, room.id, BedType.TWIN.name, BedSubType.UPPER.name)
                        self.add_bed(session, room.id, BedType.TWIN.name, BedSubType.LOWER.name)

                else:  # family
                    # One large bed and one or two bunk sets
                    bed_type = random.choice([BedType.QUEEN, BedType.KING])
                    self.add_bed(session, room.id, bed_type.name, BedSubType.REGULAR.name)
                    num_bunks = random.randint(1, 2)
                    for _ in range(num_bunks):
                        self.add_bed(session, room.id, BedType.TWIN.name, BedSubType.UPPER.name)
                        self.add_bed(session, room.id, BedType.TWIN.name, BedSubType.LOWER.name)

        return property

    def search_properties(self, session: Session, name: Optional[str] = None,
                         address: Optional[str] = None) -> List[Property]:
        """Search for properties by name or address"""
        query = session.query(Property)
        if name:
            query = query.filter(Property.name.ilike(f"%{name}%"))
        if address:
            query = query.filter(Property.address.ilike(f"%{address}%"))
        return query.all()

    def get_building(self, session: Session, building_id: int) -> Optional[Building]:
        """Get a building by ID"""
        return session.get(Building, building_id)

    def update_building(self, session: Session, building_id: int, name: str) -> Building:
        """Update a building.
        Args:
            session: SQLAlchemy session
            building_id: ID of the building to update
            name: New name for the building
        Returns:
            Updated building
        """
        building = session.get(Building, building_id)
        if not building:
            raise ValueError("Building not found")
        building.name = name
        session.commit()
        session.refresh(building)
        return building

    def delete_building(self, session: Session, building_id: int) -> bool:
        """Delete a building"""
        building = session.get(Building, building_id)
        if not building:
            return False
        # Delete all rooms in the building
        for room in building.rooms:
            self.delete_room(session, room.id)
        session.delete(building)
        session.commit()
        return True

    def get_room(self, session: Session, room_id: int) -> Optional[Room]:
        """Get a room by ID"""
        return session.get(Room, room_id)

    def update_room(self, session: Session, room_id: int,
                   room_data: Dict) -> Room:
        """Update a room with validation"""
        if not room_data.get("room_number") or not room_data["room_number"].strip():
            raise ValueError("Room number is required")
        if not room_data.get("name") or not room_data["name"].strip():
            raise ValueError("Room name is required")

        room = session.get(Room, room_id)
        if not room:
            raise ValueError("Room not found")

        # Check for duplicate room number in building
        existing = session.query(Room).filter(
            and_(
                Room.building_id == room.building_id,
                Room.room_number == room_data["room_number"],
                Room.id != room_id
            )
        ).first()
        if existing:
            raise ValueError("Room with this number already exists in the building")

        room.name = room_data["name"]
        room.room_number = room_data["room_number"]
        if "amenities" in room_data:
            room.amenities = room_data["amenities"]
        session.commit()
        return room

    def update_room_amenities(self, session: Session, room_id: int, amenities: List[str]) -> Room:
        """Update room amenities.

        Args:
            session (Session): Database session
            room_id (int): ID of the room to update
            amenities (List[str]): New list of amenities

        Returns:
            Room: Updated room object

        Raises:
            ValueError: If room not found
        """
        room = session.get(Room, room_id)
        if not room:
            raise ValueError(f"Room with id {room_id} not found")

        room.amenities = amenities
        session.commit()
        return room

    def delete_room(self, session: Session, room_id: int) -> bool:
        """Delete a room"""
        room = session.get(Room, room_id)
        if not room:
            return False
        # Delete all beds in the room first
        for bed in room.beds:
            session.delete(bed)
        # Delete all reservations for this room
        for reservation in room.reservations:
            session.delete(reservation)
        session.delete(room)
        session.commit()
        return True

    def list_buildings(self, session: Session, property_id: int):
        return session.query(Building).filter_by(property_id=property_id).all()

    def list_rooms(self, session: Session, building_id: int):
        return session.query(Room).filter_by(building_id=building_id).all()

    def get_room_details(self, session: Session, room_id: int):
        room = session.get(Room, room_id)
        if room:
            return {
                'room': room,
                'beds': room.beds,
                'total_capacity': room.capacity
            }
        return None

    def delete_bed(self, session: Session, bed_id: int):
        bed = session.get(Bed, bed_id)
        if bed:
            session.delete(bed)
            session.commit()
            return True
        return False

    def get_building_details(self, session: Session, building_id: int):
        building = session.get(Building, building_id)
        if building:
            return {
                'building': building,
                'rooms': building.rooms,
                'total_rooms': len(building.rooms)
            }
        return None

    def get_property_details(self, session: Session, property_id: int):
        property = session.get(Property, property_id)
        if property:
            return {
                'property': property,
                'buildings': property.buildings,
                'total_buildings': len(property.buildings)
            }
        return None

    def add_building(self, session: Session, property_id: int, name: str) -> Building:
        """Add a building to a property.

        Args:
            session (Session): Database session
            property_id (int): ID of the property to add building to
            name (str): Name of the building

        Returns:
            Building: Created building object

        Raises:
            ValueError: If property not found or building name is empty
        """
        if not name or not name.strip():
            raise ValueError("Building name cannot be empty")

        property = session.get(Property, property_id)
        if not property:
            raise ValueError(f"Property with id {property_id} not found")

        building = Building(name=name, property_id=property_id)
        session.add(building)
        session.commit()
        session.refresh(building)
        return building

    def add_room(self, session: Session, building_id: int, name: str, room_number: str, amenities: List[str] = None) -> Room:
        """Add a room to a building.

        Args:
            session (Session): Database session
            building_id (int): ID of the building to add room to
            name (str): Name of the room
            room_number (str): Room number
            amenities (List[str], optional): List of room amenities. Defaults to None.

        Returns:
            Room: Created room object

        Raises:
            ValueError: If building not found, room number empty, or room number already exists
        """
        if not room_number or not room_number.strip():
            raise ValueError("Room number cannot be empty")

        building = session.get(Building, building_id)
        if not building:
            raise ValueError(f"Building with id {building_id} not found")

        # Check for duplicate room number in the same building
        existing_room = session.query(Room).filter(
            Room.building_id == building_id,
            Room.room_number == room_number
        ).first()
        if existing_room:
            raise ValueError(f"Room number {room_number} already exists in building {building.name}")

        room = Room(
            name=name,
            room_number=room_number,
            building_id=building_id,
            amenities=amenities or []
        )
        session.add(room)
        session.commit()
        return room

    def list_beds(self, session: Session, room_id: int) -> List[Bed]:
        """List all beds in a room"""
        room = session.get(Room, room_id)
        if not room:
            raise ValueError("Room not found")
        return room.beds
