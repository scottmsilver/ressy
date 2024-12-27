import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models import Base, Property, Building, Room, Guest, Bed, BedType, BedSubType
from api import app
from property_manager import PropertyManager
from guest_manager import GuestManager
from fastapi.testclient import TestClient

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    # Use SQLite in-memory database for testing
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for the test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """Create a test client using the test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides["get_db"] = override_get_db
    return TestClient(app)

@pytest.fixture(scope="function")
def test_property(test_db: Session):
    """Create a test property with a building and room"""
    property_manager = PropertyManager()
    
    # Create property
    property = property_manager.create_property(
        test_db,
        "Test Hotel",
        "123 Test St"
    )
    
    # Create building
    building = property_manager.create_building(
        test_db,
        property.id,
        {
            "name": "Main Building",
            "address": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "zip_code": "12345"
        }
    )
    
    # Create room
    room = property_manager.create_room(test_db, building.id, "Standard Room", "101")
    test_db.refresh(room)
    
    # Add a bed to the room
    bed = property_manager.add_bed(test_db, room.id, BedType.QUEEN, BedSubType.STANDARD)
    test_db.commit()  # Commit the bed
    test_db.refresh(bed)
    test_db.refresh(room)
    
    # Verify the bed was added correctly
    test_db.refresh(room)
    if len(room.beds) == 0:
        raise ValueError("Failed to add bed to room")
    
    return property, building, room

@pytest.fixture
def sample_guest(test_db):
    """Create a sample guest"""
    from models import Guest
    
    guest = Guest(name="John Doe", email="john@example.com", phone="1234567890")
    test_db.add(guest)
    test_db.commit()
    
    return guest
