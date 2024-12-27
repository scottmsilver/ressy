import pytest
from sqlalchemy.orm import Session
from models import Guest, GuestCreate, Family
from guest_manager import GuestManager
from datetime import datetime

def test_create_guest(test_db):
    """Test creating a guest"""
    gm = GuestManager()
    guest_data = GuestCreate(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        preferences={"room_type": "ocean_view"},
        contact_emails=["john@example.com", "john.doe@work.com"]
    )
    
    guest = gm.create_guest(test_db, guest_data)
    assert guest.name == "John Doe"
    assert guest.email == "john@example.com"
    assert guest.phone == "1234567890"
    assert guest.preferences == {"room_type": "ocean_view"}
    assert guest.contact_emails == ["john@example.com", "john.doe@work.com"]

def test_create_guest_validation(test_db):
    """Test guest creation validation"""
    gm = GuestManager()
    
    # Test empty name
    with pytest.raises(ValueError, match="At least one contact method"):
        gm.create_guest(test_db, GuestCreate(name=""))
    
    # Test missing contact info
    with pytest.raises(ValueError, match="At least one contact method"):
        gm.create_guest(test_db, GuestCreate(name="John Doe"))

def test_get_guest(test_db):
    """Test retrieving a guest by ID"""
    gm = GuestManager()
    
    # Create a guest
    guest = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    
    # Get the guest
    retrieved = gm.get_guest(test_db, guest.id)
    assert retrieved is not None
    assert retrieved.name == "John Doe"
    assert retrieved.email == "john@example.com"
    
    # Test getting non-existent guest
    non_existent = gm.get_guest(test_db, 9999)
    assert non_existent is None

def test_find_guests(test_db):
    """Test finding guests with filters"""
    gm = GuestManager()
    
    # Create test guests
    gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    gm.create_guest(test_db, GuestCreate(
        name="Jane Smith",
        phone="1234567890"
    ))
    gm.create_guest(test_db, GuestCreate(
        name="Bob Johnson",
        email="bob@example.com",
        phone="0987654321"
    ))
    
    # Test finding by exact name
    guests = gm.find_guests(test_db, name="John Doe")
    assert len(guests) == 1
    assert guests[0].name == "John Doe"
    
    # Test finding by email domain
    guests = gm.find_guests(test_db, email="example.com")
    assert len(guests) == 2
    
    # Test finding by phone
    guests = gm.find_guests(test_db, phone="1234")
    assert len(guests) == 1
    assert guests[0].name == "Jane Smith"

def test_update_preferences(test_db):
    """Test updating guest preferences"""
    gm = GuestManager()
    
    # Create a guest
    guest = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    
    # Update preferences
    preferences = {
        "room_type": "suite",
        "bed_type": "king",
        "dietary": ["vegetarian"]
    }
    updated = gm.update_preferences(test_db, guest.id, preferences)
    
    assert updated.preferences == preferences

def test_merge_guests(test_db):
    """Test merging two guests"""
    gm = GuestManager()
    
    # Create two guests
    primary = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com",
        contact_emails=["john@example.com"]
    ))
    secondary = gm.create_guest(test_db, GuestCreate(
        name="John D",
        email="johnd@example.com",
        contact_emails=["johnd@example.com"]
    ))
    
    # Merge guests
    merged = gm.merge_guests(test_db, primary.id, secondary.id)
    
    # Check merged data
    assert merged.id == primary.id
    assert "johnd@example.com" in merged.contact_emails
    
    # Check secondary guest is deleted
    assert gm.get_guest(test_db, secondary.id) is None

def test_add_contact_email(test_db):
    """Test adding contact emails"""
    gm = GuestManager()
    
    # Create guest
    guest = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    
    # Add contact email
    updated = gm.add_contact_email(test_db, guest.id, "john.doe@work.com")
    assert "john.doe@work.com" in updated.contact_emails
    
    # Try adding duplicate email
    updated = gm.add_contact_email(test_db, guest.id, "john@example.com")
    assert len(updated.contact_emails) == 2  # No duplicate added

def test_create_family(test_db):
    """Test creating a family"""
    gm = GuestManager()
    
    # Create primary contact
    primary = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    
    # Create family
    family = gm.create_family(test_db, "Doe Family", primary.id)
    
    assert family.name == "Doe Family"
    assert family.primary_contact_id == primary.id
    
    # Check primary contact's family_id is set
    primary = gm.get_guest(test_db, primary.id)
    assert primary.family_id == family.id

def test_add_family_member(test_db):
    """Test adding a member to a family"""
    gm = GuestManager()
    
    # Create family with primary contact
    primary = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    family = gm.create_family(test_db, "Doe Family", primary.id)
    
    # Create and add family member
    member = gm.create_guest(test_db, GuestCreate(
        name="Jane Doe",
        email="jane@example.com"
    ))
    updated_member = gm.add_family_member(test_db, family.id, member.id)
    
    assert updated_member.family_id == family.id

def test_set_primary_contact(test_db):
    """Test setting primary contact for a family"""
    gm = GuestManager()
    
    # Create family with members
    primary = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    family = gm.create_family(test_db, "Doe Family", primary.id)
    
    member = gm.create_guest(test_db, GuestCreate(
        name="Jane Doe",
        email="jane@example.com"
    ))
    gm.add_family_member(test_db, family.id, member.id)
    
    # Change primary contact
    updated_family = gm.set_primary_contact(test_db, family.id, member.id)
    assert updated_family.primary_contact_id == member.id

def test_get_family_members(test_db):
    """Test getting family members"""
    gm = GuestManager()
    
    # Create family with members
    primary = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    family = gm.create_family(test_db, "Doe Family", primary.id)
    
    member1 = gm.create_guest(test_db, GuestCreate(
        name="Jane Doe",
        email="jane@example.com"
    ))
    member2 = gm.create_guest(test_db, GuestCreate(
        name="Jimmy Doe",
        email="jimmy@example.com"
    ))
    
    gm.add_family_member(test_db, family.id, member1.id)
    gm.add_family_member(test_db, family.id, member2.id)
    
    # Get members
    members = gm.get_family_members(test_db, family.id)
    assert len(members) == 3  # Including primary contact
    member_names = {member.name for member in members}
    assert member_names == {"John Doe", "Jane Doe", "Jimmy Doe"}

def test_duplicate_guest_handling(test_db):
    """Test handling of duplicate guest creation"""
    gm = GuestManager()
    
    # Create initial guest
    guest1 = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com",
        phone="1234567890"
    ))
    
    # Try creating duplicate guest with same email
    guest2 = gm.create_guest(test_db, GuestCreate(
        name="Johnny Doe",
        email="john@example.com",
        phone="9876543210"
    ))
    assert guest1.id == guest2.id  # Should return existing guest
    
    # Try creating duplicate with override
    guest3 = gm.create_guest(test_db, GuestCreate(
        name="Johnny Doe",
        email="john@example.com",
        phone="9876543210"
    ), override_duplicate=True)
    assert guest3.id == guest1.id
    assert guest3.name == "Johnny Doe"  # Name should be updated
    assert guest3.phone == "9876543210"  # Phone should be updated

def test_guest_reservations(test_db):
    """Test getting guest reservations"""
    gm = GuestManager()
    
    # Create a guest
    guest = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com"
    ))
    
    # Get reservations (should be empty initially)
    reservations = gm.get_guest_reservations(test_db, guest.id)
    assert len(reservations) == 0
    
    # Test with non-existent guest
    with pytest.raises(ValueError, match="Guest not found"):
        gm.get_guest_reservations(test_db, 9999)

def test_guest_preferences_management(test_db):
    """Test comprehensive guest preferences management"""
    gm = GuestManager()
    
    # Create guest with initial preferences
    guest = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com",
        preferences={"room_type": "suite"}
    ))
    
    # Test getting preferences
    prefs = gm.get_guest_preferences(test_db, guest.id)
    assert prefs == {"room_type": "suite"}
    
    # Update preferences
    updated_guest = gm.update_preferences(test_db, guest.id, {
        "room_type": "deluxe",
        "breakfast": True,
        "floor": "high"
    })
    assert updated_guest.preferences == {
        "room_type": "deluxe",
        "breakfast": True,
        "floor": "high"
    }
    
    # Test with non-existent guest
    with pytest.raises(ValueError, match="Guest not found"):
        gm.get_guest_preferences(test_db, 9999)
    
    with pytest.raises(ValueError, match="Guest not found"):
        gm.update_preferences(test_db, 9999, {})

def test_family_management_edge_cases(test_db):
    """Test edge cases in family management"""
    gm = GuestManager()
    
    # Create family and guests
    guest1 = gm.create_guest(test_db, GuestCreate(name="John Doe", email="john@example.com"))
    guest2 = gm.create_guest(test_db, GuestCreate(name="Jane Doe", email="jane@example.com"))
    
    # Create family with non-existent primary contact
    with pytest.raises(ValueError, match="Primary contact guest not found"):
        gm.create_family(test_db, "Doe Family", primary_contact_id=9999)
    
    # Create valid family
    family = gm.create_family(test_db, "Doe Family", primary_contact_id=guest1.id)
    
    # Try to set non-existent guest as primary contact
    with pytest.raises(ValueError, match="Guest not found"):
        gm.set_primary_contact(test_db, family.id, 9999)
    
    # Try to set non-family member as primary contact
    with pytest.raises(ValueError, match="Guest is not a member of this family"):
        gm.set_primary_contact(test_db, family.id, guest2.id)
    
    # Add member to non-existent family
    with pytest.raises(ValueError, match="Family not found"):
        gm.add_family_member(test_db, 9999, guest2.id)
    
    # Get members of non-existent family
    with pytest.raises(ValueError, match="Family not found"):
        gm.get_family_members(test_db, 9999)

def test_guest_contact_email_management(test_db):
    """Test management of guest contact emails"""
    gm = GuestManager()
    
    # Create guest with initial contact email
    guest = gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john@example.com",
        contact_emails=["john@example.com", "john.doe@work.com"]
    ))
    
    # Add new contact email
    updated_guest = gm.add_contact_email(test_db, guest.id, "john.doe@personal.com")
    assert "john.doe@personal.com" in updated_guest.contact_emails
    assert len(updated_guest.contact_emails) == 3
    
    # Try adding duplicate email
    updated_guest = gm.add_contact_email(test_db, guest.id, "john@example.com")
    assert len(updated_guest.contact_emails) == 3  # Should not add duplicate
    
    # Test with non-existent guest
    with pytest.raises(ValueError, match="Guest not found"):
        gm.add_contact_email(test_db, 9999, "test@example.com")

def test_find_guests_advanced(test_db):
    """Test advanced guest search functionality"""
    gm = GuestManager()
    
    # Create test guests
    gm.create_guest(test_db, GuestCreate(
        name="John Smith",
        email="john.smith@example.com",
        phone="1234567890"
    ))
    gm.create_guest(test_db, GuestCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="0987654321"
    ))
    gm.create_guest(test_db, GuestCreate(
        name="Jane Smith",
        email="jane.smith@company.com",
        phone="5555555555"
    ))
    
    # Test partial email match
    guests = gm.find_guests(test_db, email="smith")
    assert len(guests) == 2  # Should find both Smiths
    
    # Test partial phone match
    guests = gm.find_guests(test_db, phone="555")
    assert len(guests) == 1  # Should find Jane
    
    # Test combined filters
    guests = gm.find_guests(test_db, name="John Smith", email="example.com")
    assert len(guests) == 1  # Should find John Smith only
    
    # Test no matches
    guests = gm.find_guests(test_db, name="Nobody")
    assert len(guests) == 0
