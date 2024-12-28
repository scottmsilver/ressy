import pytest
from sqlalchemy.orm import Session
from models import Property, Building, Room, Bed, BedType, BedSubType, PropertyCreate, BuildingCreate
from property_manager import PropertyManager
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

def test_create_property(test_db):
    """Test creating a property"""
    pm = PropertyManager()
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    
    assert property.name == "Test Hotel"
    assert property.address == "123 Main St"

def test_create_property_validation(test_db):
    """Test property creation validation"""
    pm = PropertyManager()
    
    # Test empty name
    with pytest.raises(ValueError, match="Property name cannot be empty"):
        pm.create_property(test_db, "", "123 Main St")
    
    # Test empty address
    with pytest.raises(ValueError, match="Property address cannot be empty"):
        pm.create_property(test_db, "Test Hotel", "")

def test_list_properties(test_db):
    """Test listing properties with filters"""
    pm = PropertyManager()
    
    # Create test properties
    pm.create_property(test_db, "Beach Resort", "456 Ocean Dr")
    pm.create_property(test_db, "Mountain Lodge", "789 Peak Rd")
    pm.create_property(test_db, "City Hotel", "321 Urban St")
    
    # Test listing all properties
    properties = pm.list_properties(test_db)
    assert len(properties) == 3
    
    # Test filtering by name
    properties = pm.list_properties(test_db, name="Resort")
    assert len(properties) == 1
    assert properties[0].name == "Beach Resort"
    
    # Test filtering by address
    properties = pm.list_properties(test_db, address="Ocean")
    assert len(properties) == 1
    assert properties[0].address == "456 Ocean Dr"

def test_get_property(test_db):
    """Test retrieving a property by ID"""
    pm = PropertyManager()
    
    # Create a property
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    
    # Test getting existing property
    retrieved = pm.get_property(test_db, property.id)
    assert retrieved is not None
    assert retrieved.name == "Test Hotel"
    
    # Test getting non-existent property
    non_existent = pm.get_property(test_db, 9999)
    assert non_existent is None

def test_create_building(test_db):
    """Test creating a building"""
    pm = PropertyManager()
    
    # Create a property first
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    
    # Create a building
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    assert building.name == "North Wing"
    assert building.property_id == property.id

def test_create_building_validation(test_db):
    """Test building creation validation"""
    pm = PropertyManager()
    
    # Test with non-existent property
    with pytest.raises(ValueError, match="Property not found"):
        pm.create_building(test_db, 9999, {"name": "North Wing"})

def test_create_room(test_db):
    """Test creating a room"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    # Create room
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    assert room.name == "Ocean View Suite"
    assert room.room_number == "101"
    assert room.building_id == building.id

def test_create_room_validation(test_db):
    """Test room creation validation"""
    pm = PropertyManager()
    
    # Test with non-existent building
    with pytest.raises(ValueError, match="Building not found"):
        pm.create_room(test_db, 9999, name="Ocean View Suite", room_number="101")

def test_room_number_uniqueness(test_db):
    """Test that room numbers must be unique within a building"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    # Create first room
    pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # Try to create another room with the same number
    with pytest.raises(ValueError, match="Room number 101 already exists in this building"):
        pm.create_room(test_db, building.id, name="Mountain View Suite", room_number="101")

def test_add_bed(test_db):
    """Test adding a bed to a room"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # Add bed
    bed = pm.add_bed(test_db, room.id, "KING", "STANDARD")
    
    assert bed.room_id == room.id
    assert bed.bed_type.value == "king"
    assert bed.bed_subtype.value == "standard"

def test_add_bed_validation(test_db):
    """Test bed addition validation"""
    pm = PropertyManager()
    
    # Test with non-existent room
    with pytest.raises(ValueError, match="Room not found"):
        pm.add_bed(test_db, 9999, "KING", "REGULAR")

def test_list_rooms(test_db):
    """Test listing rooms in a building"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    # Create multiple rooms
    room1 = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    room2 = pm.create_room(test_db, building.id, name="Mountain View Room", room_number="102")
    room3 = pm.create_room(test_db, building.id, name="Garden View Room", room_number="103")
    
    # List all rooms
    rooms = pm.list_rooms(test_db, building.id)
    assert len(rooms) == 3
    
    # Verify room details
    room_numbers = {room.room_number for room in rooms}
    assert room_numbers == {"101", "102", "103"}

def test_get_room(test_db):
    """Test getting a room by ID"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    # Create a room
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # Get the room
    retrieved_room = pm.get_room(test_db, room.id)
    assert retrieved_room is not None
    assert retrieved_room.name == "Ocean View Suite"
    assert retrieved_room.room_number == "101"
    
    # Try getting non-existent room
    non_existent = pm.get_room(test_db, 9999)
    assert non_existent is None

def test_list_beds(test_db):
    """Test listing beds in a room"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # Add multiple beds
    bed1 = pm.add_bed(test_db, room.id, "KING", "STANDARD")
    bed2 = pm.add_bed(test_db, room.id, "SINGLE", "SOFA")
    
    # List beds
    beds = pm.list_beds(test_db, room.id)
    assert len(beds) == 2
    
    # Verify bed types
    bed_types = {bed.bed_type.value for bed in beds}
    assert bed_types == {"king", "single"}

def test_room_capacity(test_db):
    """Test calculating room capacity based on beds"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # Add beds with different capacities
    pm.add_bed(test_db, room.id, "KING", "STANDARD")  # Capacity: 2
    pm.add_bed(test_db, room.id, "SINGLE", "SOFA")    # Capacity: 1
    
    # Get room with beds
    room_with_beds = pm.get_room(test_db, room.id)
    
    # Calculate total capacity
    total_capacity = sum(bed.capacity for bed in room_with_beds.beds)
    assert total_capacity == 3  # 2 from KING + 1 from SINGLE

def test_add_bed_invalid_types(test_db):
    """Test adding a bed with invalid types"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # Try adding bed with invalid bed type
    with pytest.raises(KeyError):
        pm.add_bed(test_db, room.id, "INVALID_TYPE", "STANDARD")
    
    # Try adding bed with invalid subtype
    with pytest.raises(KeyError):
        pm.add_bed(test_db, room.id, "KING", "INVALID_SUBTYPE")

def test_room_with_multiple_bed_types(test_db):
    """Test room with multiple bed types"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room = pm.create_room(test_db, building.id, name="Family Suite", room_number="101")
    
    # Add various bed types
    pm.add_bed(test_db, room.id, "KING", "STANDARD")    # Capacity: 2
    pm.add_bed(test_db, room.id, "SINGLE", "STANDARD")  # Capacity: 1
    pm.add_bed(test_db, room.id, "SINGLE", "BUNK")     # Capacity: 1
    pm.add_bed(test_db, room.id, "DOUBLE", "SOFA")     # Capacity: 2
    
    # Get room with beds
    room_with_beds = pm.get_room(test_db, room.id)
    
    # Calculate total capacity
    total_capacity = sum(bed.capacity for bed in room_with_beds.beds)
    assert total_capacity == 6  # 2 + 1 + 1 + 2

def test_list_rooms_by_capacity(test_db):
    """Test listing rooms filtered by capacity"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    # Create rooms with different capacities
    room1 = pm.create_room(test_db, building.id, name="Single Room", room_number="101")
    pm.add_bed(test_db, room1.id, "SINGLE", "STANDARD")  # Capacity: 1
    
    room2 = pm.create_room(test_db, building.id, name="Double Room", room_number="102")
    pm.add_bed(test_db, room2.id, "DOUBLE", "STANDARD")  # Capacity: 2
    
    room3 = pm.create_room(test_db, building.id, name="Family Suite", room_number="103")
    pm.add_bed(test_db, room3.id, "KING", "STANDARD")    # Capacity: 2
    pm.add_bed(test_db, room3.id, "SINGLE", "SOFA")      # Capacity: 1
    
    # List all rooms
    rooms = pm.list_rooms(test_db, building.id)
    assert len(rooms) == 3
    
    # Calculate capacities
    capacities = {room.id: sum(bed.capacity for bed in room.beds) for room in rooms}
    assert capacities[room1.id] == 1
    assert capacities[room2.id] == 2
    assert capacities[room3.id] == 3

def test_delete_property_cascade(test_db):
    """Test that deleting a property cascades to all related entities"""
    pm = PropertyManager()
    
    # Create a property with building and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "Main Building"})
    room = pm.create_room(test_db, building.id, "Test Room", "101")
    pm.add_bed(test_db, room.id, "KING", "STANDARD")
    
    # Delete the property
    assert pm.delete_property(test_db, property.id) == True
    
    # Verify everything is deleted
    assert pm.get_property(test_db, property.id) is None
    assert pm.get_building(test_db, building.id) is None
    assert pm.get_room(test_db, room.id) is None

def test_update_building_validation(test_db):
    """Test building update validation"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "Main Building"})
    
    # Test non-existent building
    with pytest.raises(ValueError, match="Building not found"):
        pm.update_building(test_db, 9999, "New Name")
    
    # Test valid update
    updated = pm.update_building(test_db, building.id, "New Building Name")
    assert updated.name == "New Building Name"

def test_room_amenities(test_db):
    """Test room amenities management"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "Main Building"})
    room = pm.create_room(test_db, building.id, "Test Room", "101")
    
    # Test adding amenities
    amenities = ["WiFi", "TV", "Mini Bar"]
    updated = pm.update_room_amenities(test_db, room.id, amenities)
    assert updated.amenities == amenities
    
    # Test updating amenities
    new_amenities = ["WiFi", "TV", "Coffee Maker"]
    updated = pm.update_room_amenities(test_db, room.id, new_amenities)
    assert updated.amenities == new_amenities
    
    # Test non-existent room
    with pytest.raises(ValueError, match="Room with id .* not found"):
        pm.update_room_amenities(test_db, 9999, amenities)

def test_room_update_validation(test_db):
    """Test room update validation"""
    pm = PropertyManager()

    # Create property, building and rooms
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "Main Building"})
    room1 = pm.create_room(test_db, building.id, name="Ocean View", room_number="101")
    room2 = pm.create_room(test_db, building.id, name="Mountain View", room_number="102")

    # Test empty room number
    with pytest.raises(ValueError, match="Room number cannot be empty"):
        pm.update_room(test_db, room1.id, room_number="")

    # Test empty name
    with pytest.raises(ValueError, match="Room name cannot be empty"):
        pm.update_room(test_db, room1.id, name="")

    # Test duplicate room number
    with pytest.raises(ValueError, match="Room number 102 already exists in this building"):
        pm.update_room(test_db, room1.id, room_number="102")

    # Test non-existent room
    with pytest.raises(ValueError, match="Room not found"):
        pm.update_room(test_db, 9999, name="New Name")

    # Test successful update with all fields
    updated = pm.update_room(
        test_db, 
        room1.id, 
        name="Updated Room",
        room_number="103",
        amenities=["wifi", "tv", "ac"]
    )
    assert updated.name == "Updated Room"
    assert updated.room_number == "103"
    assert updated.amenities == ["wifi", "tv", "ac"]

    # Test partial update (only name)
    updated = pm.update_room(test_db, room1.id, name="New Name")
    assert updated.name == "New Name"
    assert updated.room_number == "103"  # unchanged
    assert updated.amenities == ["wifi", "tv", "ac"]  # unchanged

    # Test partial update (only amenities)
    updated = pm.update_room(test_db, room1.id, amenities=["wifi"])
    assert updated.name == "New Name"  # unchanged
    assert updated.room_number == "103"  # unchanged
    assert updated.amenities == ["wifi"]

def test_property_details(test_db):
    """Test property details retrieval"""
    pm = PropertyManager()
    
    # Create property with buildings
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building1 = pm.create_building(test_db, property.id, {"name": "Building 1"})
    building2 = pm.create_building(test_db, property.id, {"name": "Building 2"})
    
    # Get property details
    details = pm.get_property_details(test_db, property.id)
    assert details is not None
    assert details['property'].id == property.id
    assert len(details['buildings']) == 2
    assert details['total_buildings'] == 2
    
    # Test non-existent property
    assert pm.get_property_details(test_db, 9999) is None

def test_building_details(test_db):
    """Test building details retrieval"""
    pm = PropertyManager()
    
    # Create property and building with rooms
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "Main Building"})
    room1 = pm.create_room(test_db, building.id, "Room 1", "101")
    room2 = pm.create_room(test_db, building.id, "Room 2", "102")
    
    # Get building details
    details = pm.get_building_details(test_db, building.id)
    assert details is not None
    assert details['building'].id == building.id
    assert len(details['rooms']) == 2
    assert details['total_rooms'] == 2
    
    # Test non-existent building
    assert pm.get_building_details(test_db, 9999) is None

def test_room_details(test_db):
    """Test room details retrieval"""
    pm = PropertyManager()
    
    # Create property, building, and room with beds
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "Main Building"})
    room = pm.create_room(test_db, building.id, "Test Room", "101")
    pm.add_bed(test_db, room.id, "KING", "STANDARD")
    pm.add_bed(test_db, room.id, "SINGLE", "BUNK")
    
    # Get room details
    details = pm.get_room_details(test_db, room.id)
    assert details is not None
    assert details['room'].id == room.id
    assert len(details['beds']) == 2
    assert details['total_capacity'] > 0
    
    # Test non-existent room
    assert pm.get_room_details(test_db, 9999) is None

def test_bed_management(test_db):
    """Test bed management edge cases"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "Main Building"})
    room = pm.create_room(test_db, building.id, "Test Room", "101")
    
    # Add bed
    bed = pm.add_bed(test_db, room.id, "KING", "STANDARD")
    assert bed is not None
    
    # List beds
    beds = pm.list_beds(test_db, room.id)
    assert len(beds) == 1
    
    # Delete bed
    assert pm.delete_bed(test_db, bed.id) == True
    
    # Verify bed is deleted
    beds = pm.list_beds(test_db, room.id)
    assert len(beds) == 0
    
    # Test deleting non-existent bed
    assert pm.delete_bed(test_db, 9999) == False
    
    # Test listing beds for non-existent room
    with pytest.raises(ValueError, match="Room not found"):
        pm.list_beds(test_db, 9999)

def test_list_rooms_empty_building(test_db):
    """Test listing rooms in an empty building"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    # List rooms in empty building
    rooms = pm.list_rooms(test_db, building.id)
    assert len(rooms) == 0

def test_list_beds_empty_room(test_db):
    """Test listing beds in an empty room"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # List beds in empty room
    beds = pm.list_beds(test_db, room.id)
    assert len(beds) == 0

def test_room_capacity_no_beds(test_db):
    """Test room capacity with no beds"""
    pm = PropertyManager()
    
    # Create property, building, and room
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room = pm.create_room(test_db, building.id, name="Ocean View Suite", room_number="101")
    
    # Get room with no beds
    room = pm.get_room(test_db, room.id)
    
    # Calculate capacity
    total_capacity = sum(bed.capacity for bed in room.beds)
    assert total_capacity == 0

def test_update_property(test_db):
    """Test updating a property's details"""
    pm = PropertyManager()
    
    # Create a property
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    
    # Update name only
    updated = pm.update_property(test_db, property.id, name="New Hotel")
    assert updated.name == "New Hotel"
    assert updated.address == "123 Main St"
    
    # Update address only
    updated = pm.update_property(test_db, property.id, address="456 Side St")
    assert updated.name == "New Hotel"
    assert updated.address == "456 Side St"
    
    # Update both
    updated = pm.update_property(test_db, property.id, name="Final Hotel", address="789 Last St")
    assert updated.name == "Final Hotel"
    assert updated.address == "789 Last St"
    
    # Test validation
    with pytest.raises(ValueError, match="Property name cannot be empty"):
        pm.update_property(test_db, property.id, name="")
    
    with pytest.raises(ValueError, match="Property address cannot be empty"):
        pm.update_property(test_db, property.id, address="")
    
    with pytest.raises(ValueError, match="Property not found"):
        pm.update_property(test_db, 9999, name="Invalid")

def test_update_building(test_db):
    """Test updating a building's details"""
    pm = PropertyManager()
    
    # Create property and building
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    
    # Update name
    updated = pm.update_building(test_db, building.id, name="South Wing")
    assert updated.name == "South Wing"
    
    # Test validation
    with pytest.raises(ValueError, match="Building name cannot be empty"):
        pm.update_building(test_db, building.id, name="")
    
    with pytest.raises(ValueError, match="Building not found"):
        pm.update_building(test_db, 9999, name="Invalid")

def test_update_room(test_db):
    """Test updating a room's details"""
    pm = PropertyManager()
    
    # Create property, building and rooms
    property = pm.create_property(test_db, "Test Hotel", "123 Main St")
    building = pm.create_building(test_db, property.id, {"name": "North Wing"})
    room1 = pm.create_room(test_db, building.id, name="Ocean View", room_number="101")
    room2 = pm.create_room(test_db, building.id, name="Mountain View", room_number="102")
    
    # Update name only
    updated = pm.update_room(test_db, room1.id, name="Lake View")
    assert updated.name == "Lake View"
    assert updated.room_number == "101"
    
    # Update room number only
    updated = pm.update_room(test_db, room1.id, room_number="103")
    assert updated.name == "Lake View"
    assert updated.room_number == "103"
    
    # Update both
    updated = pm.update_room(test_db, room1.id, name="City View", room_number="104")
    assert updated.name == "City View"
    assert updated.room_number == "104"
    
    # Test validation
    with pytest.raises(ValueError, match="Room name cannot be empty"):
        pm.update_room(test_db, room1.id, name="")
    
    with pytest.raises(ValueError, match="Room number cannot be empty"):
        pm.update_room(test_db, room1.id, room_number="")
    
    with pytest.raises(ValueError, match="Room not found"):
        pm.update_room(test_db, 9999, name="Invalid")
    
    # Test room number uniqueness
    with pytest.raises(ValueError, match="Room number 102 already exists in this building"):
        pm.update_room(test_db, room1.id, room_number="102")
