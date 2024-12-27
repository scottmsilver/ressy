import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from models import (
    Guest, Room, Building, Property, Reservation, ReservationStatus, 
    GuestCreate, BuildingCreate, BedType, BedSubType, Bed
)
from reservation_manager import ReservationManager
from property_manager import PropertyManager
from guest_manager import GuestManager

@pytest.fixture
def reservation_manager():
    return ReservationManager()

@pytest.fixture
def property_manager():
    return PropertyManager()

@pytest.fixture
def guest_manager():
    return GuestManager()

@pytest.fixture
def test_property(test_db: Session, property_manager: PropertyManager):
    property = property_manager.create_property(test_db, "Test Hotel", "123 Test St")
    building = property_manager.create_building(test_db, property.id, {"name": "Main Building"})
    room = property_manager.create_room(test_db, building.id, "101", "Standard Room")
    
    # Add a bed to the room
    bed = property_manager.add_bed(test_db, room.id, BedType.QUEEN, BedSubType.STANDARD)
    test_db.commit()
    test_db.refresh(room)
    
    return property, building, room

@pytest.fixture
def test_guest(test_db: Session, guest_manager: GuestManager):
    guest_data = GuestCreate(
        name="John Doe",
        email="john@example.com",
        phone="1234567890"
    )
    guest = guest_manager.create_guest(test_db, guest_data)
    return guest

def test_create_reservation(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Act
    reservation = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        2,
        "Late check-in"
    )

    # Assert
    assert reservation is not None
    assert reservation.guest_id == guest.id
    assert reservation.room_id == room.id
    assert reservation.start_date.date() == start_date
    assert reservation.end_date.date() == end_date
    assert reservation.num_guests == 2
    assert reservation.special_requests == "Late check-in"
    assert reservation.status == ReservationStatus.CONFIRMED.value

def test_create_reservation_invalid_room(test_db: Session, reservation_manager: ReservationManager, test_guest):
    # Arrange
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Act & Assert
    with pytest.raises(ValueError, match="Room not found"):
        reservation_manager.create_reservation(
            test_db,
            guest.id,
            999,  # Invalid room_id
            start_date,
            end_date,
            2
        )

def test_create_reservation_invalid_guest(test_db: Session, reservation_manager: ReservationManager, test_property):
    # Arrange
    _, _, room = test_property
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Act & Assert
    with pytest.raises(ValueError, match="Guest not found"):
        reservation_manager.create_reservation(
            test_db,
            999,  # Invalid guest_id
            room.id,
            start_date,
            end_date,
            2
        )

def test_create_reservation_invalid_dates(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=2)
    end_date = start_date - timedelta(days=1)  # End date before start date

    # Act & Assert
    with pytest.raises(ValueError, match="End date must be after start date"):
        reservation_manager.create_reservation(
            test_db,
            guest.id,
            room.id,
            start_date,
            end_date,
            2
        )

def test_create_reservation_past_date(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() - timedelta(days=1)  # Start date in the past
    end_date = start_date + timedelta(days=2)

    # Act & Assert
    with pytest.raises(ValueError, match="Start date cannot be in the past"):
        reservation_manager.create_reservation(
            test_db,
            guest.id,
            room.id,
            start_date,
            end_date,
            2
        )

def test_create_overlapping_reservation(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=3)

    # Create first reservation
    reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        2
    )

    # Try to create overlapping reservation
    with pytest.raises(ValueError, match="Room is already booked for these dates"):
        reservation_manager.create_reservation(
            test_db,
            guest.id,
            room.id,
            start_date + timedelta(days=1),  # Overlapping dates
            end_date + timedelta(days=1),
            2
        )

def test_get_reservation(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Create reservation
    reservation = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        2
    )

    # Act
    retrieved = reservation_manager.get_reservation(test_db, reservation.id)

    # Assert
    assert retrieved is not None
    assert retrieved.id == reservation.id
    assert retrieved.guest_id == guest.id
    assert retrieved.room_id == room.id

def test_cancel_reservation(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Create reservation
    reservation = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        2
    )

    # Act
    success = reservation_manager.cancel_reservation(test_db, reservation.id)

    # Assert
    assert success is True
    cancelled = reservation_manager.get_reservation(test_db, reservation.id)
    assert cancelled.status == ReservationStatus.CANCELLED.value

def test_cancel_nonexistent_reservation(test_db: Session, reservation_manager: ReservationManager):
    # Act
    success = reservation_manager.cancel_reservation(test_db, 999)  # Non-existent reservation

    # Assert
    assert success is False

def test_get_daily_report(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    today = date.today()
    start_date = today + timedelta(days=1)
    end_date = start_date + timedelta(days=3)

    # Create a reservation
    reservation = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        2,
        "Late check-in"
    )

    # Act
    report = reservation_manager.get_daily_report(test_db, start_date + timedelta(days=1))

    # Assert
    assert len(report) == 1
    assert report[0]["reservation_id"] == reservation.id
    assert report[0]["room_id"] == room.id
    assert report[0]["guest_id"] == guest.id
    assert report[0]["num_guests"] == 2
    assert report[0]["special_requests"] == "Late check-in"

def test_get_guest_history(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)

    # Create multiple reservations for the guest with non-overlapping dates
    reservations = []
    for i in range(3):
        # Each reservation starts 5 days after the previous one ends
        reservation = reservation_manager.create_reservation(
            test_db,
            guest.id,
            room.id,
            start_date + timedelta(days=i*10),  # 10 days gap between reservations
            start_date + timedelta(days=i*10 + 3),  # Each reservation is 3 days long
            2
        )
        reservations.append(reservation)

    # Act
    history = reservation_manager.get_guest_history(test_db, guest.id)

    # Assert
    assert len(history) == 3
    # Check that reservations are ordered by start_date desc
    assert history[0].id == reservations[2].id
    assert history[1].id == reservations[1].id
    assert history[2].id == reservations[0].id

def test_create_reservation_with_max_guests(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test creating a reservation with maximum number of guests"""
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Create multiple beds to increase room capacity
    property_manager = PropertyManager()
    property_manager.add_bed(test_db, room.id, "KING", "STANDARD")  # Capacity: 2
    property_manager.add_bed(test_db, room.id, "QUEEN", "STANDARD")  # Capacity: 2
    
    # Act
    reservation = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        4,  # Maximum capacity based on beds
        "Need extra towels"
    )

    # Assert
    assert reservation is not None
    assert reservation.num_guests == 4
    assert reservation.special_requests == "Need extra towels"

def test_create_reservation_exceeds_capacity(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test that creating a reservation with too many guests fails"""
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Remove existing beds and add a single bed
    test_db.query(Bed).filter(Bed.room_id == room.id).delete()
    test_db.commit()
    
    # Create a single bed
    property_manager = PropertyManager()
    property_manager.add_bed(test_db, room.id, BedType.SINGLE, BedSubType.STANDARD)  # Capacity: 1
    test_db.commit()
    test_db.refresh(room)

    # Act & Assert
    with pytest.raises(ValueError, match="Room capacity exceeded"):
        reservation_manager.create_reservation(
            test_db,
            guest.id,
            room.id,
            start_date,
            end_date,
            2,  # Exceeds capacity of single bed
            "Need extra bed"
        )

def test_create_multiple_non_overlapping_reservations(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test creating multiple reservations for the same room with no overlap"""
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)

    # Act
    reservations = []
    # Create 3 back-to-back reservations
    for i in range(3):
        reservation = reservation_manager.create_reservation(
            test_db,
            guest.id,
            room.id,
            start_date + timedelta(days=i*2),
            start_date + timedelta(days=(i+1)*2),
            1
        )
        reservations.append(reservation)

    # Assert
    assert len(reservations) == 3
    for i, res in enumerate(reservations):
        assert res.start_date.date() == start_date + timedelta(days=i*2)
        assert res.end_date.date() == start_date + timedelta(days=(i+1)*2)

def test_get_reservation_nonexistent(test_db: Session, reservation_manager: ReservationManager):
    """Test getting a non-existent reservation returns None"""
    # Act
    reservation = reservation_manager.get_reservation(test_db, 999)

    # Assert
    assert reservation is None

def test_create_reservation_same_day(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test creating a reservation where check-out is same day as check-in"""
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date  # Same day

    # Act & Assert
    with pytest.raises(ValueError, match="End date must be after start date"):
        reservation_manager.create_reservation(
            test_db,
            guest.id,
            room.id,
            start_date,
            end_date,
            1
        )

def test_create_reservation_far_future(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test creating a reservation far in the future"""
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=365)  # One year from now
    end_date = start_date + timedelta(days=5)

    # Act
    reservation = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        1
    )

    # Assert
    assert reservation is not None
    assert reservation.start_date.date() == start_date
    assert reservation.end_date.date() == end_date

def test_get_daily_report_empty(test_db: Session, reservation_manager: ReservationManager):
    """Test getting daily report when no reservations exist"""
    # Act
    report = reservation_manager.get_daily_report(test_db, date.today())

    # Assert
    assert len(report) == 0

def test_get_daily_report_multiple_rooms(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test daily report with multiple rooms and reservations"""
    # Arrange
    property, building, room1 = test_property
    
    # Create a second room
    property_manager = PropertyManager()
    room2 = property_manager.create_room(test_db, building.id, "102", "Deluxe Room")
    
    # Add beds to the second room
    property_manager.add_bed(test_db, room2.id, BedType.KING, BedSubType.STANDARD)  # Capacity: 2
    property_manager.add_bed(test_db, room2.id, BedType.QUEEN, BedSubType.STANDARD)  # Capacity: 2
    test_db.commit()
    test_db.refresh(room2)

    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=3)
    
    # Create reservations for both rooms
    reservation1 = reservation_manager.create_reservation(
        test_db,
        test_guest.id,
        room1.id,
        start_date,
        end_date,
        1,
        "Room 1 request"
    )
    
    reservation2 = reservation_manager.create_reservation(
        test_db,
        test_guest.id,
        room2.id,
        start_date,
        end_date,
        2,
        "Room 2 request"
    )

    # Act
    report = reservation_manager.get_daily_report(test_db, start_date + timedelta(days=1))

    # Assert
    assert len(report) == 2
    room_ids = {r["room_id"] for r in report}
    assert room_ids == {room1.id, room2.id}

def test_cancel_and_rebook(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test canceling a reservation and rebooking the same room"""
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)

    # Create and cancel first reservation
    reservation1 = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        1
    )
    reservation_manager.cancel_reservation(test_db, reservation1.id)

    # Act - Create new reservation for same period
    reservation2 = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        end_date,
        1
    )

    # Assert
    assert reservation2 is not None
    assert reservation2.id != reservation1.id
    assert reservation2.start_date.date() == start_date
    assert reservation2.end_date.date() == end_date

def test_get_guest_history_no_reservations(test_db: Session, reservation_manager: ReservationManager, test_guest):
    """Test getting history for a guest with no reservations"""
    # Act
    history = reservation_manager.get_guest_history(test_db, test_guest.id)

    # Assert
    assert len(history) == 0

def test_get_guest_history_with_cancelled(test_db: Session, reservation_manager: ReservationManager, test_property, test_guest):
    """Test guest history includes cancelled reservations"""
    # Arrange
    _, _, room = test_property
    guest = test_guest
    start_date = date.today() + timedelta(days=1)

    # Create and cancel a reservation
    reservation1 = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date,
        start_date + timedelta(days=2),
        1
    )
    reservation_manager.cancel_reservation(test_db, reservation1.id)

    # Create another active reservation
    reservation2 = reservation_manager.create_reservation(
        test_db,
        guest.id,
        room.id,
        start_date + timedelta(days=10),
        start_date + timedelta(days=12),
        1
    )

    # Act
    history = reservation_manager.get_guest_history(test_db, guest.id)

    # Assert
    assert len(history) == 2
    assert any(r.status == ReservationStatus.CANCELLED.value for r in history)
    assert any(r.status == ReservationStatus.CONFIRMED.value for r in history)
