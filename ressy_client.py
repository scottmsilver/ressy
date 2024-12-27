import requests
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class RessyClient:
    """Client for interacting with the Ressy API"""
    base_url: str = "http://localhost:8000"

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a GET request to the API"""
        response = requests.get(f"{self.base_url}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Dict) -> Dict:
        """Make a POST request to the API"""
        response = requests.post(f"{self.base_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def _put(self, endpoint: str, data: Dict) -> Dict:
        """Make a PUT request to the API"""
        response = requests.put(f"{self.base_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def _delete(self, endpoint: str) -> Dict:
        """Make a DELETE request to the API"""
        response = requests.delete(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()

    # Property Management
    def create_property(self, name: str, address: str) -> Dict:
        """Create a new property"""
        return self._post("properties", {"name": name, "address": address})

    def list_properties(self, name: str = None, address: str = None) -> List[Dict]:
        """List all properties with optional filters"""
        params = {}
        if name:
            params["name"] = name
        if address:
            params["address"] = address
        return self._get("properties", params)

    def get_property(self, property_id: int) -> Dict:
        """Get a property by ID"""
        return self._get(f"properties/{property_id}")

    def delete_property(self, property_id: int) -> Dict:
        """Delete a property"""
        return self._delete(f"properties/{property_id}")

    # Building Management
    def create_building(self, property_id: int, name: str) -> Dict:
        """Create a new building"""
        return self._post(f"properties/{property_id}/buildings", {"name": name})

    def list_buildings(self, property_id: int) -> List[Dict]:
        """List all buildings in a property"""
        return self._get(f"properties/{property_id}/buildings")

    def delete_building(self, building_id: int) -> Dict:
        """Delete a building"""
        return self._delete(f"buildings/{building_id}")

    def update_building(self, building_id: int, name: str) -> Dict:
        """Update a building"""
        return self._put(f"buildings/{building_id}", {"name": name})

    # Room Management
    def create_room(self, building_id: int, name: str, room_number: str) -> Dict:
        """Create a new room"""
        return self._post(f"buildings/{building_id}/rooms", {
            "name": name,
            "room_number": room_number
        })

    def list_rooms(self, building_id: int) -> List[Dict]:
        """List all rooms in a building"""
        return self._get(f"buildings/{building_id}/rooms")

    def delete_room(self, room_id: int) -> Dict:
        """Delete a room"""
        return self._delete(f"rooms/{room_id}")

    def update_room_amenities(self, room_id: int, amenities: List[str]) -> Dict:
        """Update room amenities"""
        return self._put(f"rooms/{room_id}/amenities", {"amenities": amenities})

    # Bed Management
    def create_bed(self, room_id: int, bed_type: str, bed_subtype: str) -> Dict:
        """Create a new bed"""
        return self._post(f"rooms/{room_id}/beds", {
            "bed_type": bed_type,
            "bed_subtype": bed_subtype
        })

    def list_beds(self, room_id: int) -> List[Dict]:
        """List all beds in a room"""
        return self._get(f"rooms/{room_id}/beds")

    def delete_bed(self, bed_id: int) -> Dict:
        """Delete a bed"""
        return self._delete(f"beds/{bed_id}")

    # Guest Management
    def create_guest(self, name: str, email: Optional[str] = None, phone: Optional[str] = None) -> Dict:
        """Create a new guest"""
        data = {"name": name}
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        return self._post("guests", data)

    def get_guest(self, guest_id: int) -> Dict:
        """Get a guest by ID"""
        return self._get(f"guests/{guest_id}")

    def search_guests(self, name: str = None, email: str = None, phone: str = None) -> List[Dict]:
        """Search for guests"""
        params = {}
        if name:
            params["name"] = name
        if email:
            params["email"] = email
        if phone:
            params["phone"] = phone
        return self._get("guests/search", params)

    def update_guest_preferences(self, guest_id: int, preferences: Dict) -> Dict:
        """Update guest preferences"""
        return self._put(f"guests/{guest_id}/preferences", preferences)

    # Reservation Management
    def create_reservation(self, guest_id: int, room_id: int, start_date: date, end_date: date, num_guests: int = 1) -> Dict:
        """Create a new reservation"""
        return self._post("reservations", {
            "guest_id": guest_id,
            "room_id": room_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "num_guests": num_guests
        })

    def get_reservation(self, reservation_id: int) -> Dict:
        """Get a reservation by ID"""
        return self._get(f"reservations/{reservation_id}")

    def cancel_reservation(self, reservation_id: int) -> Dict:
        """Cancel a reservation"""
        return self._post(f"reservations/{reservation_id}/cancel", {})

    def check_room_availability(self, room_id: int, start_date: date, end_date: date) -> Dict:
        """Check if a room is available for given dates"""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        return self._get(f"rooms/{room_id}/availability", params)

    def get_property_availability(self, property_id: int, start_date: date, end_date: date) -> Dict:
        """Get property availability for a date range"""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        return self._get(f"properties/{property_id}/availability", params)

    def get_daily_report(self, report_date: date) -> Dict:
        """Get daily occupancy report"""
        return self._get("reports/daily", {"date": report_date.isoformat()})

    def get_property_report(self, property_id: int, start_date: date, end_date: date) -> Dict:
        """Get a comprehensive property report"""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        return self._get(f"properties/{property_id}/report", params)
