from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, cast, Date
from models import Reservation, Room, Guest, ReservationStatus, Bed, BedType, Building
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

class ReservationManager:
    def create_reservation(
        self, session: Session, guest_id: int, room_id: int, 
        start_date: date, end_date: date, num_guests: int,
        special_requests: Optional[str] = None
    ) -> Reservation:
        """Create a new reservation"""
        # Validate dates
        if start_date >= end_date:
            raise ValueError("End date must be after start date")
        if start_date < date.today():
            raise ValueError("Start date cannot be in the past")

        # Check if room exists
        room = session.query(Room).options(joinedload(Room.beds)).filter(Room.id == room_id).first()
        if not room:
            raise ValueError("Room not found")

        # Check if guest exists
        guest = session.query(Guest).filter(Guest.id == guest_id).first()
        if not guest:
            raise ValueError("Guest not found")

        # Check room capacity using room's beds relationship
        total_capacity = sum(2 if bed.bed_type in [BedType.KING, BedType.QUEEN] else 1 for bed in room.beds)
        if num_guests > total_capacity:
            raise ValueError("Room capacity exceeded")

        # Check room availability
        if not self.check_room_availability(session, room_id, start_date, end_date):
            raise ValueError("Room is not available for the requested dates")

        # Convert dates to datetime at midnight UTC
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.min.time())

        # Create reservation
        reservation = Reservation(
            guest_id=guest_id,
            room_id=room_id,
            start_date=start_datetime,
            end_date=end_datetime,
            num_guests=num_guests,
            special_requests=special_requests,
            status=ReservationStatus.CONFIRMED.value
        )
        session.add(reservation)
        session.commit()
        session.refresh(reservation)
        return reservation

    def get_reservation(self, session: Session, reservation_id: int) -> Optional[Reservation]:
        """Get a reservation by ID"""
        return session.get(Reservation, reservation_id)

    def cancel_reservation(self, session: Session, reservation_id: int) -> bool:
        """Cancel a reservation"""
        reservation = session.get(Reservation, reservation_id)
        if not reservation:
            return False
        reservation.status = ReservationStatus.CANCELLED.value
        session.commit()
        return True

    def check_room_availability(self, session: Session, room_id: int, start_date: date, end_date: date) -> bool:
        """Check if room is available for the given dates"""
        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.min.time())

        # Check for overlapping reservations
        overlapping = session.query(Reservation).filter(
            Reservation.room_id == room_id,
            Reservation.start_date < end_datetime,
            Reservation.end_date > start_datetime,
            Reservation.status == ReservationStatus.CONFIRMED.value
        ).first()

        if overlapping:
            raise ValueError("Room is already booked for these dates")
        return True

    def get_daily_report(self, session: Session, report_date: date) -> List[Dict]:
        """Get occupancy report for a specific date"""
        # Convert report_date to datetime at midnight UTC for proper comparison
        report_start = datetime.combine(report_date, datetime.min.time())
        report_end = datetime.combine(report_date + timedelta(days=1), datetime.min.time())
        
        # Get reservations for the specific date
        reservations = session.query(Reservation).filter(
            Reservation.start_date < report_end,
            Reservation.end_date > report_start,
            Reservation.status == ReservationStatus.CONFIRMED.value
        ).all()

        report = []
        for res in reservations:
            report.append({
                "reservation_id": res.id,
                "room_id": res.room_id,
                "guest_id": res.guest_id,
                "num_guests": res.num_guests,
                "start_date": res.start_date.date().isoformat(),
                "end_date": res.end_date.date().isoformat(),
                "special_requests": res.special_requests
            })
        return report

    def get_guest_history(self, session: Session, guest_id: int) -> List[Reservation]:
        """Get reservation history for a guest"""
        return session.query(Reservation).filter(
            Reservation.guest_id == guest_id
        ).order_by(Reservation.start_date.desc()).all()

    def get_property_reservations(
        self,
        session: Session,
        property_id: int,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Get all reservations for a property in a date range"""
        # Get all rooms in the property
        rooms = (
            session.query(Room)
            .join(Building)
            .filter(Building.property_id == property_id)
            .all()
        )

        room_ids = [room.id for room in rooms]

        # Get reservations for these rooms
        reservations = (
            session.query(Reservation)
            .filter(
                Reservation.room_id.in_(room_ids),
                Reservation.start_date <= end_date,
                Reservation.end_date >= start_date,
                Reservation.status != ReservationStatus.CANCELLED.value
            )
            .all()
        )

        return {
            'total_rooms': len(room_ids),
            'reservations': reservations
        }
