from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Guest, Family, GuestCreate, Reservation
from typing import List, Optional, Dict, Any

class GuestManager:
    def create_guest(self, session: Session, guest: GuestCreate, override_duplicate: bool = False) -> Guest:
        """Create a new guest"""
        if not guest.email and not guest.phone:
            raise ValueError("At least one contact method (email or phone) must be provided")

        # Check for existing guest with same contact info
        existing_guest = None
        query = session.query(Guest)
        conditions = []
        if guest.email:
            conditions.append(Guest.email == guest.email)
        if guest.phone:
            conditions.append(Guest.phone == guest.phone)
        if conditions:
            existing_guest = query.filter(or_(*conditions)).first()

        if existing_guest:
            if override_duplicate:
                # Update existing guest with new data
                existing_guest.name = guest.name
                existing_guest.preferences = guest.preferences or existing_guest.preferences
                existing_guest.contact_emails = guest.contact_emails or existing_guest.contact_emails
                if guest.email and guest.email not in existing_guest.contact_emails:
                    existing_guest.add_contact_email(guest.email)
                if guest.phone:
                    existing_guest.phone = guest.phone
                existing_guest.family_id = guest.family_id
                session.commit()
                session.refresh(existing_guest)
                return existing_guest
            else:
                # Return existing guest without changes
                return existing_guest

        # Create a new guest
        db_guest = Guest(
            name=guest.name,
            email=guest.email,
            phone=guest.phone,
            preferences=guest.preferences or {},
            family_id=guest.family_id
        )
        if guest.contact_emails:
            for email in guest.contact_emails:
                db_guest.add_contact_email(email)
        session.add(db_guest)
        session.commit()
        session.refresh(db_guest)
        return db_guest

    def get_guest(self, session: Session, guest_id: int) -> Optional[Guest]:
        """Get a guest by ID"""
        return session.get(Guest, guest_id)

    def find_guests(self, session: Session, name: Optional[str] = None, 
                   email: Optional[str] = None, phone: Optional[str] = None) -> List[Guest]:
        """Find guests by name, email, or phone.

        Args:
            session (Session): Database session
            name (Optional[str], optional): Guest name to search for. Defaults to None.
            email (Optional[str], optional): Guest email to search for. Defaults to None.
            phone (Optional[str], optional): Guest phone to search for. Defaults to None.

        Returns:
            List[Guest]: List of matching guests
        """
        query = session.query(Guest)
        if name:
            query = query.filter(Guest.name == name)
        if email:
            query = query.filter(Guest.email.ilike(f"%{email}%"))
        if phone:
            query = query.filter(Guest.phone.ilike(f"%{phone}%"))
        return query.all()

    def update_preferences(self, session: Session, guest_id: int, preferences: dict) -> Guest:
        """Update guest preferences"""
        guest = session.get(Guest, guest_id)
        if not guest:
            raise ValueError("Guest not found")
        guest.preferences = preferences
        session.commit()
        session.refresh(guest)
        return guest

    def merge_guests(self, session: Session, primary_guest_id: int, secondary_guest_id: int) -> Guest:
        """Merge two guests, keeping the primary guest and deleting the secondary guest.
        All reservations and family relationships from the secondary guest will be transferred
        to the primary guest."""
        if primary_guest_id == secondary_guest_id:
            raise ValueError("Cannot merge a guest with itself")

        primary_guest = session.get(Guest, primary_guest_id)
        secondary_guest = session.get(Guest, secondary_guest_id)

        if not primary_guest or not secondary_guest:
            raise ValueError("One or both guests not found")

        # Update contact information
        if secondary_guest.email:
            primary_guest.add_contact_email(secondary_guest.email)
        
        # Merge contact emails
        if secondary_guest.contact_emails:
            for email in secondary_guest.contact_emails:
                primary_guest.add_contact_email(email)
        
        # Transfer reservations
        for reservation in secondary_guest.reservations:
            reservation.guest_id = primary_guest_id

        # Handle family relationships
        if secondary_guest.family_id and not primary_guest.family_id:
            primary_guest.family_id = secondary_guest.family_id
        elif secondary_guest.family_id and secondary_guest.family_id != primary_guest.family_id:
            # Move all family members to primary guest's family
            for member in session.query(Guest).filter_by(family_id=secondary_guest.family_id).all():
                member.family_id = primary_guest.family_id
            # Delete the old family
            session.query(Family).filter_by(id=secondary_guest.family_id).delete()

        # Delete the secondary guest
        session.delete(secondary_guest)
        session.commit()
        session.refresh(primary_guest)
        return primary_guest

    def add_contact_email(self, session: Session, guest_id: int, email: str) -> Guest:
        """Add a contact email to guest"""
        guest = session.get(Guest, guest_id)
        if not guest:
            raise ValueError("Guest not found")
        
        guest.add_contact_email(email)
        session.commit()
        session.refresh(guest)
        return guest

    def create_family(self, session: Session, name: str, 
                     primary_contact_id: Optional[int] = None) -> Family:
        """Create a new family"""
        family = Family(name=name)
        session.add(family)
        session.flush()  # Get the family ID
        
        if primary_contact_id:
            # Get the guest and set them as primary contact
            guest = session.get(Guest, primary_contact_id)
            if not guest:
                raise ValueError("Primary contact guest not found")
            
            # Set the guest's family_id first
            guest.family_id = family.id
            session.flush()
            
            # Then set them as primary contact
            family.primary_contact_id = primary_contact_id
            session.flush()
        
        session.commit()
        session.refresh(family)
        return family

    def add_family_member(self, session: Session, family_id: int, guest_id: int) -> Guest:
        """Add a guest to a family"""
        family = session.get(Family, family_id)
        if not family:
            raise ValueError("Family not found")

        guest = session.get(Guest, guest_id)
        if not guest:
            raise ValueError("Guest not found")

        guest.family_id = family_id
        session.commit()
        session.refresh(guest)
        session.refresh(family)
        return guest

    def set_primary_contact(self, session: Session, family_id: int, guest_id: int) -> Family:
        """Set the primary contact for a family"""
        family = session.get(Family, family_id)
        guest = session.get(Guest, guest_id)
        if not family:
            raise ValueError("Family not found")
        if not guest:
            raise ValueError("Guest not found")
        if guest.family_id != family_id:
            raise ValueError("Guest is not a member of this family")
        family.primary_contact_id = guest_id
        session.commit()
        session.refresh(family)
        return family

    def get_family_members(self, session: Session, family_id: int) -> List[Guest]:
        """Get all members of a family"""
        family = session.get(Family, family_id)
        if not family:
            raise ValueError("Family not found")
            
        return family.guests

    def get_guest_reservations(self, session: Session, guest_id: int) -> List[Reservation]:
        """Get all reservations for a guest"""
        guest = session.get(Guest, guest_id)
        if not guest:
            raise ValueError("Guest not found")
            
        return guest.reservations

    def get_guest_preferences(self, session: Session, guest_id: int) -> Dict[str, Any]:
        """Get guest preferences"""
        guest = session.get(Guest, guest_id)
        if not guest:
            raise ValueError("Guest not found")
        return guest.preferences
