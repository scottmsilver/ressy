import pytest
from sqlalchemy.orm import Session
from models import Room, Bed, BedType, BedSubType
from property_manager import PropertyManager

def test_room_bed_capacity(test_db: Session, test_property):
    """Test that room capacity is correctly calculated based on beds"""
    # Arrange
    _, _, room = test_property
    test_db.refresh(room)
    
    # Debug output
    print(f"\nRoom ID: {room.id}")
    print(f"Number of beds: {len(room.beds)}")
    for bed in room.beds:
        print(f"Bed ID: {bed.id}, Type: {bed.bed_type}, Subtype: {bed.bed_subtype}")
    
    # Verify the bed exists in a separate query
    bed_count = test_db.query(Room).filter(Room.id == room.id).join(Room.beds).count()
    print(f"Direct bed count from query: {bed_count}")
    
    # Act & Assert
    # At this point, the room should have one QUEEN bed from the fixture
    assert len(room.beds) == 1, f"Expected 1 bed, but found {len(room.beds)}"
    assert room.beds[0].bed_type == BedType.QUEEN, f"Expected QUEEN bed, but found {room.beds[0].bed_type}"
    assert room.capacity == 2, f"Expected capacity 2 for QUEEN bed, but got {room.capacity}"
    
    # Verify we can query the bed directly
    assert bed_count == 1, f"Expected 1 bed from direct query, but got {bed_count}"

def test_add_multiple_beds(test_db: Session, test_property):
    """Test adding multiple beds to a room"""
    # Arrange
    property_manager = PropertyManager()
    _, _, room = test_property
    
    # Add another bed
    property_manager.add_bed(test_db, room.id, BedType.SINGLE, BedSubType.STANDARD)
    test_db.refresh(room)
    
    # Debug output
    print(f"\nAfter adding SINGLE bed:")
    print(f"Room ID: {room.id}")
    print(f"Number of beds: {len(room.beds)}")
    for bed in room.beds:
        print(f"Bed ID: {bed.id}, Type: {bed.bed_type}, Subtype: {bed.bed_subtype}")
    
    # Verify we now have 2 beds (QUEEN from fixture + new SINGLE)
    assert len(room.beds) == 2, f"Expected 2 beds, but found {len(room.beds)}"
    
    # Verify the capacity is correct (2 for QUEEN + 1 for SINGLE = 3)
    assert room.capacity == 3, f"Expected capacity 3, but got {room.capacity}"
    
    # Add one more bed
    property_manager.add_bed(test_db, room.id, BedType.KING, BedSubType.STANDARD)
    test_db.refresh(room)
    
    print(f"\nAfter adding KING bed:")
    print(f"Number of beds: {len(room.beds)}")
    for bed in room.beds:
        print(f"Bed ID: {bed.id}, Type: {bed.bed_type}, Subtype: {bed.bed_subtype}")
    
    # Verify we now have 3 beds
    assert len(room.beds) == 3, f"Expected 3 beds, but found {len(room.beds)}"
    
    # Verify the capacity is correct (2 for QUEEN + 1 for SINGLE + 2 for KING = 5)
    assert room.capacity == 5, f"Expected capacity 5, but got {room.capacity}"
