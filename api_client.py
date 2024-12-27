import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ApiClient:
    """Client for interacting with the Ressy API"""
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, params=data)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            elif method == "PUT":
                response = requests.put(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            if response.status_code != 204:  # No content
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'json'):
                error_detail = e.response.json().get('detail', str(e))
            else:
                error_detail = str(e)
            raise Exception(f"API Error: {error_detail}")

    # Property operations
    def create_property(self, name: str, address: str) -> Dict:
        return self._make_request("POST", "/properties/", {"name": name, "address": address})

    def list_properties(self) -> List[Dict]:
        return self._make_request("GET", "/properties/")

    def get_property(self, property_id: int) -> Dict:
        return self._make_request("GET", f"/properties/{property_id}")

    def delete_property(self, property_id: int) -> None:
        return self._make_request("DELETE", f"/properties/{property_id}")

    def generate_random_property(self) -> Dict:
        return self._make_request("POST", "/properties/random")

    # Building operations
    def create_building(self, property_id: int, name: str) -> Dict:
        return self._make_request("POST", f"/properties/{property_id}/buildings/", {"name": name})

    def list_buildings(self, property_id: int) -> List[Dict]:
        return self._make_request("GET", f"/properties/{property_id}/buildings/")

    def delete_building(self, building_id: int) -> None:
        return self._make_request("DELETE", f"/buildings/{building_id}")

    # Room operations
    def create_room(self, building_id: int, name: str, room_number: str) -> Dict:
        return self._make_request("POST", f"/buildings/{building_id}/rooms/", 
                                {"name": name, "room_number": room_number})

    def list_rooms(self, building_id: int) -> List[Dict]:
        return self._make_request("GET", f"/buildings/{building_id}/rooms/")

    def delete_room(self, room_id: int) -> None:
        return self._make_request("DELETE", f"/rooms/{room_id}")

    # Bed operations
    def create_bed(self, room_id: int, bed_type: str, bed_subtype: str) -> Dict:
        """Create a new bed in a room"""
        return self._make_request("POST", f"/rooms/{room_id}/beds/", {
            "bed_type": bed_type,
            "bed_subtype": bed_subtype
        })

    def list_beds(self, room_id: int) -> List[Dict]:
        """List all beds in a room"""
        return self._make_request("GET", f"/rooms/{room_id}/beds/")

    def delete_bed(self, bed_id: int) -> None:
        """Delete a bed"""
        return self._make_request("DELETE", f"/beds/{bed_id}")

    # Guest Management
    def create_guest(self, name, email=None, phone=None, override_duplicate=False):
        """Create a new guest"""
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "override_duplicate": override_duplicate
        }
        return self._make_request("POST", "/guests/", data)

    def get_guest(self, guest_id):
        """Get a guest by ID"""
        return self._make_request("GET", f"/guests/{guest_id}")

    def find_guests(self, email=None, phone=None, name=None):
        """Find guests by email, phone, or name"""
        params = {}
        if email:
            params["email"] = email
        if phone:
            params["phone"] = phone
        if name:
            params["name"] = name
        return self._make_request("GET", "/guests/", params)

    def create_family(self, name, primary_contact_id=None):
        """Create a new family"""
        data = {
            "name": name,
            "primary_contact_id": primary_contact_id
        }
        return self._make_request("POST", "/families/", data)

    def add_to_family(self, guest_id, family_id):
        """Add a guest to a family"""
        return self._make_request("POST", f"/families/{family_id}/members/{guest_id}")

    def set_primary_contact(self, family_id, guest_id):
        """Set the primary contact for a family"""
        return self._make_request("PUT", f"/families/{family_id}/primary-contact/{guest_id}")

    def get_family_members(self, family_id):
        """Get all members of a family"""
        return self._make_request("GET", f"/families/{family_id}/members")

    def get_guest_reservations(self, guest_id, include_cancelled=False):
        """Get all reservations for a guest"""
        return self._make_request("GET", f"/guests/{guest_id}/reservations", {"include_cancelled": include_cancelled})

    # Reservation Management
    def create_reservation(self, guest_id: int, room_id: int, start_date: str, end_date: str, 
                         num_guests: int = 1, special_requests: Optional[str] = None) -> Dict:
        """Create a new reservation"""
        data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "start_date": start_date,
            "end_date": end_date,
            "num_guests": num_guests,
            "special_requests": special_requests
        }
        return self._make_request("POST", "/reservations/", data)

    def get_reservation(self, reservation_id: int) -> Dict:
        """Get a reservation by ID"""
        return self._make_request("GET", f"/reservations/{reservation_id}")

    def cancel_reservation(self, reservation_id: int) -> Dict:
        """Cancel a reservation"""
        return self._make_request("POST", f"/reservations/{reservation_id}/cancel")

    def check_room_availability(self, room_id: int, start_date: str, end_date: str) -> Dict:
        """Check if a room is available for given dates"""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return self._make_request("GET", f"/rooms/{room_id}/availability", params)

    def get_daily_report(self, report_date: str) -> Dict:
        """Get occupancy report for a specific date"""
        return self._make_request("GET", f"/reports/daily/{report_date}")

    def get_property_availability(self, property_id: int, start_date: str, end_date: str) -> Dict:
        """Get availability report for an entire property"""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return self._make_request("GET", f"/properties/{property_id}/availability", params)
