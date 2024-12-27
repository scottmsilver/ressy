#!/usr/bin/env python3
from datetime import datetime, date
import sys
from typing import Optional, List, Dict
from ressy_client import RessyClient
from tabulate import tabulate

class RessyCLI:
    def __init__(self, server_url: str = "http://localhost:8000"):
        """Initialize the CLI with a server URL"""
        self.client = RessyClient(server_url)
        self.current_property = None
        self.current_building = None
        self.current_room = None
        self.navigation_path = []

    def update_navigation(self, item_type: str, item_name: str = None):
        """Update the navigation path"""
        if item_name:
            self.navigation_path.append(f"{item_type}: {item_name}")
        else:
            self.navigation_path = self.navigation_path[:-1]

    def print_navigation(self):
        """Print the current navigation path"""
        if self.navigation_path:
            path = " > ".join(self.navigation_path)
            print(f"\nRessy > {path}")

    def print_menu(self, title: str, options: list):
        """Print a menu with numbered options"""
        self.print_navigation()
        print(f"\n{title}")
        print("=" * len(title))
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        print("0. Back/Exit")

    def get_choice(self, max_choice: int) -> int:
        """Get user's choice with validation"""
        while True:
            try:
                choice = input("\nEnter your choice: ")
                if choice.lower() == 'q':
                    sys.exit(0)
                choice = int(choice)
                if 0 <= choice <= max_choice:
                    return choice
                print(f"Please enter a number between 0 and {max_choice}")
            except ValueError:
                print("Please enter a valid number")

    def get_date_input(self, prompt: str) -> date:
        """Get a date input from user"""
        while True:
            try:
                date_str = input(prompt + " (YYYY-MM-DD): ")
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("Please enter a valid date in YYYY-MM-DD format")

    def format_table(self, headers: List[str], rows: List[List[str]], title: str = None) -> None:
        """Format and print a table using tabulate"""
        if title:
            print(f"\n{title}")
        print(tabulate(rows, headers=headers, tablefmt="grid"))

    def manage_properties(self):
        """Property management menu"""
        self.update_navigation("Properties")
        while True:
            options = [
                "Create Property",
                "List Properties",
                "Select Property",
                "Delete Property",
                "View Property Report"
            ]
            self.print_menu("Property Management", options)
            choice = self.get_choice(len(options))

            if choice == 0:
                self.update_navigation("Properties", None)
                return
            elif choice == 1:  # Create Property
                name = input("Enter property name: ")
                address = input("Enter property address: ")
                try:
                    property = self.client.create_property(name, address)
                    print(f"Created property: {property['name']}")
                except Exception as e:
                    print(f"Error creating property: {e}")
            elif choice == 2:  # List Properties
                try:
                    properties = self.client.list_properties()
                    headers = ["ID", "Name", "Address", "Buildings", "Rooms"]
                    rows = []
                    for p in properties:
                        num_buildings = len(p.get('buildings', []))
                        num_rooms = sum(len(b.get('rooms', [])) for b in p.get('buildings', []))
                        rows.append([
                            p['id'],
                            p['name'][:30],
                            p['address'][:30],
                            num_buildings,
                            num_rooms
                        ])
                    self.format_table(headers, rows, "Properties")
                except Exception as e:
                    print(f"Error listing properties: {e}")
            elif choice == 3:  # Select Property
                try:
                    property_id = int(input("Enter property ID: "))
                    self.current_property = self.client.get_property(property_id)
                    self.manage_buildings()
                except ValueError:
                    print("Please enter a valid property ID")
                except Exception as e:
                    print(f"Error selecting property: {e}")
            elif choice == 4:  # Delete Property
                try:
                    property_id = int(input("Enter property ID to delete: "))
                    self.client.delete_property(property_id)
                    print("Property deleted successfully")
                except Exception as e:
                    print(f"Error deleting property: {e}")
            elif choice == 5:  # View Property Report
                try:
                    property_id = int(input("Enter property ID: "))
                    start_date = self.get_date_input("Enter start date")
                    end_date = self.get_date_input("Enter end date")
                    report = self.client.get_property_report(property_id, start_date, end_date)
                    print("\nProperty Report:")
                    print(f"Total Rooms: {report['total_rooms']}")
                    print(f"Occupied Rooms: {report['occupied_rooms']}")
                    print(f"Occupancy Rate: {report['occupancy_rate']}%")
                    print(f"Revenue: ${report['revenue']}")
                except Exception as e:
                    print(f"Error getting property report: {e}")

    def manage_buildings(self):
        """Building management menu"""
        self.update_navigation("Property", self.current_property['name'])
        while True:
            options = [
                "Create Building",
                "List Buildings",
                "Select Building",
                "Delete Building",
                "Update Building"
            ]
            self.print_menu(f"Building Management", options)
            choice = self.get_choice(len(options))

            if choice == 0:
                self.update_navigation("Property", None)
                return
            elif choice == 1:  # Create Building
                name = input("Enter building name: ")
                try:
                    building = self.client.create_building(self.current_property['id'], name)
                    print(f"Created building: {building['name']}")
                except Exception as e:
                    print(f"Error creating building: {e}")
            elif choice == 2:  # List Buildings
                try:
                    buildings = self.client.list_buildings(self.current_property['id'])
                    headers = ["ID", "Name", "Rooms"]
                    rows = []
                    for b in buildings:
                        rows.append([
                            b['id'],
                            b['name'][:30],
                            len(b.get('rooms', []))
                        ])
                    self.format_table(headers, rows, "Buildings")
                except Exception as e:
                    print(f"Error listing buildings: {e}")
            elif choice == 3:  # Select Building
                try:
                    building_id = int(input("Enter building ID: "))
                    self.current_building = next(
                        b for b in self.client.list_buildings(self.current_property['id'])
                        if b['id'] == building_id
                    )
                    self.manage_rooms()
                except (ValueError, StopIteration):
                    print("Invalid building ID")
                except Exception as e:
                    print(f"Error selecting building: {e}")
            elif choice == 4:  # Delete Building
                try:
                    building_id = int(input("Enter building ID to delete: "))
                    self.client.delete_building(building_id)
                    print("Building deleted successfully")
                except Exception as e:
                    print(f"Error deleting building: {e}")
            elif choice == 5:  # Update Building
                try:
                    building_id = int(input("Enter building ID: "))
                    name = input("Enter new building name: ")
                    self.client.update_building(building_id, name)
                    print("Building updated successfully")
                except Exception as e:
                    print(f"Error updating building: {e}")

    def manage_rooms(self):
        """Room management menu"""
        self.update_navigation("Building", self.current_building['name'])
        while True:
            options = [
                "Create Room",
                "List Rooms",
                "Select Room",
                "Delete Room",
                "Update Room Amenities",
                "Check Room Availability"
            ]
            self.print_menu(f"Room Management", options)
            choice = self.get_choice(len(options))

            if choice == 0:
                self.update_navigation("Building", None)
                return
            elif choice == 1:  # Create Room
                name = input("Enter room name: ")
                room_number = input("Enter room number: ")
                try:
                    room = self.client.create_room(self.current_building['id'], name, room_number)
                    print(f"Created room: {room['name']}")
                except Exception as e:
                    print(f"Error creating room: {e}")
            elif choice == 2:  # List Rooms
                try:
                    rooms = self.client.list_rooms(self.current_building['id'])
                    headers = ["ID", "Name", "Room Number", "Amenities", "Beds"]
                    rows = []
                    for r in rooms:
                        amenities = ", ".join(r.get('amenities', []))[:30]
                        rows.append([
                            r['id'],
                            r['name'][:30],
                            r['room_number'],
                            amenities,
                            len(r.get('beds', []))
                        ])
                    self.format_table(headers, rows, "Rooms")
                except Exception as e:
                    print(f"Error listing rooms: {e}")
            elif choice == 3:  # Select Room
                try:
                    room_id = int(input("Enter room ID: "))
                    self.current_room = next(
                        r for r in self.client.list_rooms(self.current_building['id'])
                        if r['id'] == room_id
                    )
                    self.manage_beds()
                except (ValueError, StopIteration):
                    print("Invalid room ID")
                except Exception as e:
                    print(f"Error selecting room: {e}")
            elif choice == 4:  # Delete Room
                try:
                    room_id = int(input("Enter room ID to delete: "))
                    self.client.delete_room(room_id)
                    print("Room deleted successfully")
                except Exception as e:
                    print(f"Error deleting room: {e}")
            elif choice == 5:  # Update Room Amenities
                try:
                    room_id = int(input("Enter room ID: "))
                    amenities = input("Enter amenities (comma-separated): ").split(',')
                    amenities = [a.strip() for a in amenities if a.strip()]
                    self.client.update_room_amenities(room_id, amenities)
                    print("Room amenities updated successfully")
                except Exception as e:
                    print(f"Error updating room amenities: {e}")
            elif choice == 6:  # Check Room Availability
                try:
                    room_id = int(input("Enter room ID: "))
                    start_date = self.get_date_input("Enter start date")
                    end_date = self.get_date_input("Enter end date")
                    availability = self.client.check_room_availability(room_id, start_date, end_date)
                    if availability['available']:
                        print("Room is available for the selected dates")
                    else:
                        print("Room is not available for the selected dates")
                        if 'conflicts' in availability:
                            print("\nConflicting reservations:")
                            for conflict in availability['conflicts']:
                                print(f"- {conflict['start_date']} to {conflict['end_date']}")
                except Exception as e:
                    print(f"Error checking room availability: {e}")

    def manage_beds(self):
        """Bed management menu"""
        self.update_navigation("Room", self.current_room['name'])
        while True:
            options = [
                "Add Bed",
                "List Beds",
                "Delete Bed"
            ]
            self.print_menu(f"Bed Management", options)
            choice = self.get_choice(len(options))

            if choice == 0:
                self.update_navigation("Room", None)
                return
            elif choice == 1:  # Add Bed
                print("\nBed Types: TWIN, QUEEN, KING")
                print("Bed Subtypes: REGULAR, UPPER, LOWER")
                bed_type = input("Enter bed type: ").upper()
                bed_subtype = input("Enter bed subtype: ").upper()
                try:
                    bed = self.client.create_bed(self.current_room['id'], bed_type, bed_subtype)
                    print(f"Added {bed_type} bed")
                except Exception as e:
                    print(f"Error adding bed: {e}")
            elif choice == 2:  # List Beds
                try:
                    beds = self.client.list_beds(self.current_room['id'])
                    headers = ["ID", "Type", "Subtype", "Capacity"]
                    rows = []
                    for b in beds:
                        rows.append([
                            b['id'],
                            b['bed_type'],
                            b['bed_subtype'],
                            b.get('capacity', '-')
                        ])
                    self.format_table(headers, rows, "Beds")
                except Exception as e:
                    print(f"Error listing beds: {e}")
            elif choice == 3:  # Delete Bed
                try:
                    bed_id = int(input("Enter bed ID to delete: "))
                    self.client.delete_bed(bed_id)
                    print("Bed deleted successfully")
                except Exception as e:
                    print(f"Error deleting bed: {e}")

    def manage_guests(self):
        """Guest management menu"""
        self.update_navigation("Guests")
        while True:
            options = [
                "Create Guest",
                "Search Guests",
                "View Guest Details",
                "Update Guest Preferences"
            ]
            self.print_menu("Guest Management", options)
            choice = self.get_choice(len(options))

            if choice == 0:
                self.update_navigation("Guests", None)
                return
            elif choice == 1:  # Create Guest
                name = input("Enter guest name: ")
                email = input("Enter guest email (optional): ") or None
                phone = input("Enter guest phone (optional): ") or None
                try:
                    guest = self.client.create_guest(name, email, phone)
                    print(f"Created guest: {guest['name']}")
                except Exception as e:
                    print(f"Error creating guest: {e}")
            elif choice == 2:  # Search Guests
                name = input("Enter guest name (optional): ") or None
                email = input("Enter guest email (optional): ") or None
                phone = input("Enter guest phone (optional): ") or None
                try:
                    guests = self.client.search_guests(name, email, phone)
                    headers = ["ID", "Name", "Email", "Phone", "Preferences"]
                    rows = []
                    for g in guests:
                        prefs = ", ".join(f"{k}: {v}" for k, v in g.get('preferences', {}).items())[:30]
                        rows.append([
                            g['id'],
                            g['name'][:30],
                            g.get('email', '-')[:30],
                            g.get('phone', '-')[:15],
                            prefs
                        ])
                    self.format_table(headers, rows, "Guests Found")
                except Exception as e:
                    print(f"Error searching guests: {e}")
            elif choice == 3:  # View Guest Details
                try:
                    guest_id = int(input("Enter guest ID: "))
                    guest = self.client.get_guest(guest_id)
                    print(f"\nGuest Details:")
                    print(f"Name: {guest['name']}")
                    print(f"Email: {guest['email']}")
                    print(f"Phone: {guest['phone']}")
                    print("Preferences:", guest.get('preferences', {}))
                except Exception as e:
                    print(f"Error getting guest details: {e}")
            elif choice == 4:  # Update Guest Preferences
                try:
                    guest_id = int(input("Enter guest ID: "))
                    preferences = {}
                    while True:
                        key = input("Enter preference key (or empty to finish): ")
                        if not key:
                            break
                        value = input(f"Enter value for {key}: ")
                        preferences[key] = value
                    self.client.update_guest_preferences(guest_id, preferences)
                    print("Guest preferences updated successfully")
                except Exception as e:
                    print(f"Error updating guest preferences: {e}")

    def manage_reservations(self):
        """Reservation management menu"""
        self.update_navigation("Reservations")
        while True:
            options = [
                "Create Reservation",
                "View Reservation",
                "Cancel Reservation",
                "Check Property Availability"
            ]
            self.print_menu("Reservation Management", options)
            choice = self.get_choice(len(options))

            if choice == 0:
                self.update_navigation("Reservations", None)
                return
            elif choice == 1:  # Create Reservation
                try:
                    guest_id = int(input("Enter guest ID: "))
                    room_id = int(input("Enter room ID: "))
                    start_date = self.get_date_input("Enter check-in date")
                    end_date = self.get_date_input("Enter check-out date")
                    num_guests = int(input("Enter number of guests: "))
                    reservation = self.client.create_reservation(
                        guest_id, room_id, start_date, end_date, num_guests
                    )
                    print(f"Created reservation: ID {reservation['id']}")
                except Exception as e:
                    print(f"Error creating reservation: {e}")
            elif choice == 2:  # View Reservation
                try:
                    reservation_id = int(input("Enter reservation ID: "))
                    reservation = self.client.get_reservation(reservation_id)
                    print(f"\nReservation Details:")
                    print(f"ID: {reservation['id']}")
                    print(f"Guest ID: {reservation['guest_id']}")
                    print(f"Room ID: {reservation['room_id']}")
                    print(f"Check-in: {reservation['start_date']}")
                    print(f"Check-out: {reservation['end_date']}")
                    print(f"Number of guests: {reservation['num_guests']}")
                    print(f"Status: {reservation['status']}")
                except Exception as e:
                    print(f"Error viewing reservation: {e}")
            elif choice == 3:  # Cancel Reservation
                try:
                    reservation_id = int(input("Enter reservation ID to cancel: "))
                    self.client.cancel_reservation(reservation_id)
                    print("Reservation cancelled successfully")
                except Exception as e:
                    print(f"Error cancelling reservation: {e}")
            elif choice == 4:  # Check Property Availability
                try:
                    property_id = int(input("Enter property ID: "))
                    start_date = self.get_date_input("Enter start date")
                    end_date = self.get_date_input("Enter end date")
                    availability = self.client.get_property_availability(
                        property_id, start_date, end_date
                    )
                    print(f"\nProperty Availability:")
                    print(f"Total Rooms: {availability['total_rooms']}")
                    
                    if availability['available_rooms']:
                        headers = ["Room Number", "Name", "Building"]
                        rows = []
                        for room in availability['available_rooms']:
                            rows.append([
                                room['room_number'],
                                room['name'][:30],
                                room.get('building_name', '-')[:30]
                            ])
                        self.format_table(headers, rows, "Available Rooms")
                except Exception as e:
                    print(f"Error checking property availability: {e}")

    def main_menu(self):
        """Main menu loop"""
        while True:
            options = [
                "Property Management",
                "Guest Management",
                "Reservation Management"
            ]
            self.print_menu("Ressy Property Management System", options)
            choice = self.get_choice(len(options))

            if choice == 0:
                print("Goodbye!")
                sys.exit(0)
            elif choice == 1:
                self.manage_properties()
            elif choice == 2:
                self.manage_guests()
            elif choice == 3:
                self.manage_reservations()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Ressy Property Management CLI')
    parser.add_argument('--server', default='http://localhost:8000',
                      help='Server URL (default: http://localhost:8000)')
    args = parser.parse_args()
    
    print(f"Connecting to Ressy server at: {args.server}")
    cli = RessyCLI(args.server)
    try:
        cli.main_menu()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError connecting to server: {e}")
        sys.exit(1)
