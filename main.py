from api_client import ApiClient
from models import BedType, BedSubType
import subprocess
import requests
import signal
import os
import time
from typing import Optional
import argparse
from contextlib import contextmanager
from datetime import datetime, date, timedelta

class ApiServerManager:
    def __init__(self, private: bool = False):
        self.server_process: Optional[subprocess.Popen] = None
        self.base_url = "http://localhost:8000"
        self.private = private
        self._port = 8000
        
    @property
    def port(self) -> int:
        return self._port
        
    def find_available_port(self) -> int:
        """Find an available port starting from 8000"""
        import socket
        port = 8000
        while port < 9000:  # Limit the search to avoid infinite loop
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return port
                except OSError:
                    port += 1
        raise RuntimeError("No available ports found between 8000-9000")
    
    def start_server(self) -> bool:
        if self.server_process:
            print("Server is already running")
            return True
            
        try:
            if self.private:
                self._port = self.find_available_port()
                self.base_url = f"http://localhost:{self._port}"
            
            print(f"Starting server on port {self._port}...")
            uvicorn_path = os.path.join("venv", "bin", "uvicorn")
            if not os.path.exists(uvicorn_path):
                print(f"Error: {uvicorn_path} not found. Please ensure virtual environment is set up correctly.")
                return False
                
            self.server_process = subprocess.Popen(
                [uvicorn_path, "api:app", "--host", "127.0.0.1", "--port", str(self._port), "--log-level", "debug"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for server to start
            max_retries = 30
            retries = 0
            while retries < max_retries:
                try:
                    response = requests.get(f"{self.base_url}/docs")
                    if response.status_code == 200:
                        print(f"Server started successfully on {self.base_url}")
                        return True
                except requests.RequestException:
                    retries += 1
                    time.sleep(1)
                    print(f"Waiting for server to start... ({retries}/{max_retries})")
                    
                    # Check if process has failed
                    if self.server_process.poll() is not None:
                        error_output = self.server_process.stderr.read().decode()
                        print(f"Server process failed to start. Error: {error_output}")
                        return False
            
            print("Failed to start server after maximum retries")
            self.stop_server()
            return False
        except Exception as e:
            print(f"Error starting server: {str(e)}")
            if self.server_process and self.server_process.stderr:
                error_output = self.server_process.stderr.read().decode()
                print(f"Server error output: {error_output}")
            return False
    
    def stop_server(self) -> bool:
        if not self.server_process:
            print("No server is running")
            return True
            
        try:
            os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            self.server_process = None
            return True
        except Exception as e:
            print(f"Error stopping server: {str(e)}")
            return False
    
    def check_server(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/docs")
            return response.status_code == 200
        except:
            return False
    
    def get_status(self) -> str:
        is_running = self.check_server()
        mode = "private" if self.private else "shared"
        if is_running:
            return f" API Server ({mode}) is running at {self.base_url}"
        else:
            return f" API Server ({mode}) is not running"

@contextmanager
def managed_api_server(private: bool = False):
    """Context manager for automatically managing API server lifecycle"""
    server = ApiServerManager(private=private)
    try:
        if not server.start_server():
            raise RuntimeError("Failed to start API server")
        yield server
    finally:
        server.stop_server()

def format_date(d: str) -> str:
    """Format date for display"""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%B %d, %Y")
    except:
        return d

def get_date_input(prompt: str) -> str:
    """Get a date input from user in YYYY-MM-DD format"""
    while True:
        date_str = input(prompt)
        if not date_str:
            return None
        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD")

def manage_rooms(api_client, building_id, building_name):
    while True:
        print(f"\nManaging Rooms in Building: {building_name}")
        print("1. Add Room")
        print("2. List Rooms")
        print("3. Add Bed to Room")
        print("4. Remove Bed")
        print("5. Remove Room")
        print("6. Back to Building Menu")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            name = input("Enter room name: ")
            number = input("Enter room number: ")
            room = api_client.create_room(building_id, name, number)
            print(f"Room added with ID: {room['id']}")
            
            add_beds = input("Would you like to add beds to this room? (y/n): ")
            if add_beds.lower() == 'y':
                while True:
                    print("\nBed Types:")
                    print("1. Twin")
                    print("2. Queen")
                    print("3. King")
                    bed_type_choice = input("Choose bed type (1-3) or 'done' to finish: ")
                    
                    if bed_type_choice.lower() == 'done':
                        break
                        
                    try:
                        bed_type_choice = int(bed_type_choice)
                        if bed_type_choice not in [1, 2, 3]:
                            print("Invalid choice. Please choose 1-3.")
                            continue
                            
                        bed_type = {
                            1: "TWIN",
                            2: "QUEEN",
                            3: "KING"
                        }[bed_type_choice]
                        
                        is_bunk = input("Is this a bunk bed? (y/n): ").lower() == 'y'
                        if is_bunk:
                            print("\nBunk Bed Position:")
                            print("1. Upper")
                            print("2. Lower")
                            position = input("Choose position (1-2): ")
                            subtype = "UPPER" if position == "1" else "LOWER"
                        else:
                            subtype = "REGULAR"
                            
                        api_client.create_bed(room['id'], bed_type, subtype)
                        print("Bed added successfully")
                        
                    except ValueError:
                        print("Invalid input. Please enter a number.")

        elif choice == "2":
            rooms = api_client.list_rooms(building_id)
            for room in rooms:
                print(f"\nID: {room['id']}, Name: {room['name']}, Number: {room['room_number']}")
                print(f"Total Capacity: {room['capacity']}")
                if room['beds']:
                    print("  Beds:")
                    for bed in room['beds']:
                        bunk_info = f" ({bed['bed_subtype']})" if bed['bed_subtype'] != "REGULAR" else ""
                        print(f"    - ID: {bed['id']}, {bed['bed_type']}{bunk_info} (Capacity: {bed['capacity']})")

        elif choice == "3":
            rooms = api_client.list_rooms(building_id)
            if not rooms:
                print("No rooms available. Please add a room first.")
                continue
                
            print("\nAvailable Rooms:")
            for room in rooms:
                print(f"ID: {room['id']}, Name: {room['name']}, Number: {room['room_number']}")
            
            room_id = int(input("Enter room ID to add bed to: "))
            
            print("\nBed Types:")
            print("1. Twin")
            print("2. Queen")
            print("3. King")
            bed_type_choice = int(input("Choose bed type (1-3): "))
            
            bed_type = {
                1: "TWIN",
                2: "QUEEN",
                3: "KING"
            }[bed_type_choice]
            
            is_bunk = input("Is this a bunk bed? (y/n): ").lower() == 'y'
            if is_bunk:
                print("\nBunk Bed Position:")
                print("1. Upper")
                print("2. Lower")
                position = input("Choose position (1-2): ")
                subtype = "UPPER" if position == "1" else "LOWER"
            else:
                subtype = "REGULAR"
                
            api_client.create_bed(room_id, bed_type, subtype)
            print("Bed added successfully")

        elif choice == "4":
            rooms = api_client.list_rooms(building_id)
            if not rooms:
                print("No rooms available.")
                continue
                
            print("\nSelect a room to remove a bed from:")
            for room in rooms:
                print(f"\nRoom {room['room_number']}: {room['name']}")
                if room['beds']:
                    print("  Beds:")
                    for bed in room['beds']:
                        bunk_info = f" ({bed['bed_subtype']})" if bed['bed_subtype'] != "REGULAR" else ""
                        print(f"    - ID: {bed['id']}, {bed['bed_type']}{bunk_info}")
            
            bed_id = int(input("\nEnter bed ID to remove: "))
            confirm = input("Are you sure you want to remove this bed? (y/n): ")
            if confirm.lower() == 'y':
                api_client.delete_bed(bed_id)
                print("Bed removed successfully")

        elif choice == "5":
            rooms = api_client.list_rooms(building_id)
            if not rooms:
                print("No rooms available.")
                continue
                
            print("\nAvailable Rooms:")
            for room in rooms:
                print(f"ID: {room['id']}, Name: {room['name']}, Number: {room['room_number']}")
            
            room_id = int(input("Enter room ID to remove: "))
            confirm = input("This will remove all beds in the room. Are you sure? (y/n): ")
            if confirm.lower() == 'y':
                api_client.delete_room(room_id)
                print("Room and all its beds removed successfully")

        elif choice == "6":
            break

def manage_buildings(api_client, property_id, property_name):
    while True:
        print(f"\nManaging Buildings in Property: {property_name}")
        print("1. Add Building")
        print("2. List Buildings")
        print("3. Manage Rooms in Building")
        print("4. Remove Building")
        print("5. Back to Property Menu")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            name = input("Enter building name: ")
            building = api_client.create_building(property_id, name)
            print(f"Building added with ID: {building['id']}")
            
            manage_now = input("Would you like to manage rooms in this building now? (y/n): ")
            if manage_now.lower() == 'y':
                manage_rooms(api_client, building['id'], building['name'])

        elif choice == "2":
            buildings = api_client.list_buildings(property_id)
            for building in buildings:
                print(f"\nID: {building['id']}, Name: {building['name']}")
                print(f"Total Rooms: {len(building['rooms'])}")
                for room in building['rooms']:
                    print(f"  - Room {room['room_number']}: {room['name']} (Capacity: {room['capacity']})")

        elif choice == "3":
            buildings = api_client.list_buildings(property_id)
            if not buildings:
                print("No buildings available. Please add a building first.")
                continue
                
            print("\nAvailable Buildings:")
            for building in buildings:
                print(f"ID: {building['id']}, Name: {building['name']}")
            
            building_id = int(input("Enter building ID to manage: "))
            building = next((b for b in buildings if b['id'] == building_id), None)
            if building:
                manage_rooms(api_client, building['id'], building['name'])
            else:
                print("Invalid building ID")

        elif choice == "4":
            buildings = api_client.list_buildings(property_id)
            if not buildings:
                print("No buildings available.")
                continue
                
            print("\nAvailable Buildings:")
            for building in buildings:
                print(f"ID: {building['id']}, Name: {building['name']}")
                print(f"Total Rooms: {len(building['rooms'])}")
            
            building_id = int(input("Enter building ID to remove: "))
            confirm = input("This will remove all rooms and beds in the building. Are you sure? (y/n): ")
            if confirm.lower() == 'y':
                api_client.delete_building(building_id)
                print("Building and all its contents removed successfully")

        elif choice == "5":
            break

def display_property(api_client, property_id):
    """Display a property and all its details in a nicely formatted way."""
    property_data = api_client.get_property(property_id)
    
    print("\n" + "="*50)
    print(f"Property: {property_data['name']}")
    print(f"Address: {property_data['address']}")
    print("="*50)
    
    if not property_data.get('buildings'):
        print("No buildings in this property.")
        return
        
    for building in property_data['buildings']:
        print(f"\n Building: {building['name']}")
        
        if not building.get('rooms'):
            print("  No rooms in this building.")
            continue
            
        for room in building['rooms']:
            print(f"\n  Room {room['room_number']} - {room['name']}")
            if room.get('amenities'):
                print("    Amenities:", ", ".join(room['amenities']))
            
            # Get beds in room
            beds = api_client.list_beds(room['id'])
            if beds:
                print("    Beds:")
                for bed in beds:
                    print(f"      • {bed['bed_type'].title()} ({bed['bed_subtype'].title()})")
    print("\n" + "="*50)

def manage_properties(api_client):
    while True:
        print("\nProperty Management")
        print("1. Add Property")
        print("2. List Properties")
        print("3. Manage Property")
        print("4. Remove Property")
        print("5. Display Property Details")
        print("6. Back to Main Menu")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            name = input("Enter property name: ")
            address = input("Enter property address: ")
            property = api_client.create_property(name, address)
            print(f"Property added with ID: {property['id']}")
            
            manage_now = input("Would you like to manage buildings in this property now? (y/n): ")
            if manage_now.lower() == 'y':
                manage_buildings(api_client, property['id'], property['name'])

        elif choice == "2":
            properties = api_client.list_properties()
            for property in properties:
                print(f"\nID: {property['id']}, Name: {property['name']}")
                print(f"Address: {property['address']}")
                print(f"Total Buildings: {len(property['buildings'])}")
                for building in property['buildings']:
                    print(f"  - {building['name']}: {len(building['rooms'])} rooms")

        elif choice == "3":
            properties = api_client.list_properties()
            if not properties:
                print("No properties available. Please add a property first.")
                continue
                
            print("\nAvailable Properties:")
            for property in properties:
                print(f"ID: {property['id']}, Name: {property['name']}")
            
            property_id = int(input("Enter property ID to manage: "))
            property = next((p for p in properties if p['id'] == property_id), None)
            if property:
                manage_buildings(api_client, property['id'], property['name'])
            else:
                print("Invalid property ID")

        elif choice == "4":
            properties = api_client.list_properties()
            if not properties:
                print("No properties available.")
                continue
                
            print("\nAvailable Properties:")
            for property in properties:
                print(f"ID: {property['id']}, Name: {property['name']}")
                print(f"Address: {property['address']}")
                print(f"Total Buildings: {len(property['buildings'])}")
            
            property_id = int(input("Enter property ID to remove: "))
            confirm = input("This will remove all buildings, rooms, and beds in the property. Are you sure? (y/n): ")
            if confirm.lower() == 'y':
                api_client.delete_property(property_id)
                print("Property and all its contents removed successfully")

        elif choice == "5":
            properties = api_client.list_properties()
            if not properties:
                print("No properties found.")
                continue
                
            print("\nAvailable Properties:")
            for prop in properties:
                print(f"{prop['id']}. {prop['name']}")
                
            prop_id = input("\nEnter property ID to display (or press Enter to go back): ")
            if not prop_id:
                continue
                
            try:
                prop_id = int(prop_id)
                display_property(api_client, prop_id)
            except ValueError:
                print("Invalid property ID")
            except Exception as e:
                print(f"Error displaying property: {str(e)}")

        elif choice == "6":
            break

def manage_guests(api_client):
    while True:
        print("\nGuest Management")
        print("1. Create Guest")
        print("2. Find Guests")
        print("3. View Guest Details")
        print("4. Create Family")
        print("5. Add Guest to Family")
        print("6. View Family Members")
        print("7. Set Primary Family Contact")
        print("8. Back")

        try:
            choice = input("Enter your choice (1-8): ")

            if choice == "1":
                name = input("Enter guest name: ")
                email = input("Enter email (optional, press Enter to skip): ").strip() or None
                phone = input("Enter phone (optional, press Enter to skip): ").strip() or None
                
                if not email and not phone:
                    print("Error: Either email or phone must be provided")
                    continue

                try:
                    guest = api_client.create_guest(name, email, phone)
                    print(f"\nGuest created successfully!")
                    print(f"ID: {guest['id']}")
                    print(f"Name: {guest['name']}")
                    print(f"Email: {guest['email']}")
                    print(f"Phone: {guest['phone']}")
                except Exception as e:
                    if "already exists" in str(e):
                        override = input("Guest with this contact info exists. Override? (y/n): ")
                        if override.lower() == 'y':
                            guest = api_client.create_guest(name, email, phone, override_duplicate=True)
                            print(f"\nGuest created successfully with override!")
                    else:
                        print(f"Error: {str(e)}")

            elif choice == "2":
                print("\nSearch by:")
                print("1. Name")
                print("2. Email")
                print("3. Phone")
                search_choice = input("Enter choice (1-3): ")
                
                if search_choice == "1":
                    name = input("Enter name to search: ")
                    guests = api_client.find_guests(name=name)
                elif search_choice == "2":
                    email = input("Enter email to search: ")
                    guests = api_client.find_guests(email=email)
                elif search_choice == "3":
                    phone = input("Enter phone to search: ")
                    guests = api_client.find_guests(phone=phone)
                else:
                    print("Invalid choice")
                    continue

                if guests:
                    print("\nFound guests:")
                    for guest in guests:
                        print(f"\nID: {guest['id']}")
                        print(f"Name: {guest['name']}")
                        print(f"Email: {guest['email']}")
                        print(f"Phone: {guest['phone']}")
                        if guest['family_id']:
                            print(f"Family ID: {guest['family_id']}")
                else:
                    print("No guests found")

            elif choice == "3":
                guest_id = input("Enter guest ID: ")
                try:
                    guest = api_client.get_guest(int(guest_id))
                    print(f"\nGuest Details:")
                    print(f"ID: {guest['id']}")
                    print(f"Name: {guest['name']}")
                    print(f"Email: {guest['email']}")
                    print(f"Phone: {guest['phone']}")
                    if guest['family_id']:
                        print(f"Family ID: {guest['family_id']}")
                    
                    # Show reservations
                    reservations = api_client.get_guest_reservations(int(guest_id))
                    if reservations:
                        print("\nReservations:")
                        for res in reservations:
                            print(f"\nReservation ID: {res['id']}")
                            print(f"Check-in: {res['check_in_date']}")
                            print(f"Check-out: {res['check_out_date']}")
                            print(f"Number of guests: {res['num_guests']}")
                except Exception as e:
                    print(f"Error: {str(e)}")

            elif choice == "4":
                name = input("Enter family name: ")
                try:
                    family = api_client.create_family(name)
                    print(f"\nFamily created successfully!")
                    print(f"ID: {family['id']}")
                    print(f"Name: {family['name']}")
                except Exception as e:
                    print(f"Error: {str(e)}")

            elif choice == "5":
                family_id = input("Enter family ID: ")
                guest_id = input("Enter guest ID: ")
                try:
                    guest = api_client.add_to_family(int(guest_id), int(family_id))
                    print(f"\nGuest {guest['name']} added to family {family_id}")
                except Exception as e:
                    print(f"Error: {str(e)}")

            elif choice == "6":
                family_id = input("Enter family ID: ")
                try:
                    members = api_client.get_family_members(int(family_id))
                    if members:
                        print("\nFamily members:")
                        for member in members:
                            print(f"\nID: {member['id']}")
                            print(f"Name: {member['name']}")
                            print(f"Email: {member['email']}")
                            print(f"Phone: {member['phone']}")
                    else:
                        print("No family members found")
                except Exception as e:
                    print(f"Error: {str(e)}")

            elif choice == "7":
                family_id = input("Enter family ID: ")
                guest_id = input("Enter guest ID for primary contact: ")
                try:
                    family = api_client.set_primary_contact(int(family_id), int(guest_id))
                    print(f"\nPrimary contact set for family {family['name']}")
                except Exception as e:
                    print(f"Error: {str(e)}")

            elif choice == "8":
                break
            else:
                print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def manage_reservations(api_client):
    while True:
        print("\nReservation Management")
        print("1. Create Reservation")
        print("2. View Reservation")
        print("3. Cancel Reservation")
        print("4. View Guest Reservations")
        print("5. Check Room Availability")
        print("6. View Property Availability")
        print("7. View Daily Occupancy Report")
        print("8. Back to Main Menu")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == "1":
            # Get guest
            guest_id = None
            while not guest_id:
                search_term = input("Enter guest name, email, or phone (or press Enter to go back): ")
                if not search_term:
                    break
                    
                guests = api_client.find_guests(name=search_term)
                if not guests:
                    print("No guests found. Please try again.")
                    continue
                    
                print("\nFound guests:")
                for i, guest in enumerate(guests, 1):
                    print(f"{i}. {guest['name']} (ID: {guest['id']})")
                    
                selection = input("\nSelect guest number (or press Enter to search again): ")
                if selection.isdigit() and 1 <= int(selection) <= len(guests):
                    guest_id = guests[int(selection)-1]['id']
            
            if not guest_id:
                continue
            
            # Get property and room
            properties = api_client.list_properties()
            if not properties:
                print("No properties available.")
                continue
                
            print("\nAvailable Properties:")
            for i, prop in enumerate(properties, 1):
                print(f"{i}. {prop['name']}")
                
            prop_choice = input("\nSelect property number: ")
            if not prop_choice.isdigit() or not 1 <= int(prop_choice) <= len(properties):
                print("Invalid selection")
                continue
                
            property_id = properties[int(prop_choice)-1]['id']
            
            # Get dates
            start_date = get_date_input("Enter check-in date (YYYY-MM-DD): ")
            if not start_date:
                continue
                
            end_date = get_date_input("Enter check-out date (YYYY-MM-DD): ")
            if not end_date:
                continue
            
            # Show available rooms
            try:
                availability = api_client.get_property_availability(property_id, start_date, end_date)
                if not availability['available_rooms']:
                    print("No rooms available for these dates.")
                    continue
                    
                print("\nAvailable Rooms:")
                for i, room in enumerate(availability['available_rooms'], 1):
                    print(f"{i}. Room {room['room_number']} - {room['name']}")
                    
                room_choice = input("\nSelect room number: ")
                if not room_choice.isdigit() or not 1 <= int(room_choice) <= len(availability['available_rooms']):
                    print("Invalid selection")
                    continue
                    
                room_id = availability['available_rooms'][int(room_choice)-1]['id']
                
                # Get additional details
                num_guests = input("Enter number of guests (default: 1): ")
                num_guests = int(num_guests) if num_guests.isdigit() else 1
                
                special_requests = input("Enter any special requests (optional): ")
                
                # Create reservation
                reservation = api_client.create_reservation(
                    guest_id=guest_id,
                    room_id=room_id,
                    start_date=start_date,
                    end_date=end_date,
                    num_guests=num_guests,
                    special_requests=special_requests if special_requests else None
                )
                
                print(f"\nReservation created successfully!")
                print(f"Reservation ID: {reservation['id']}")
                print(f"Guest: {reservation['guest_name']}")
                print(f"Room: {reservation['room_name']}")
                print(f"Dates: {format_date(reservation['start_date'])} - {format_date(reservation['end_date'])}")
                
            except Exception as e:
                print(f"Error: {str(e)}")
                
        elif choice == "2":
            res_id = input("Enter reservation ID: ")
            if not res_id.isdigit():
                print("Invalid reservation ID")
                continue
                
            try:
                reservation = api_client.get_reservation(int(res_id))
                print("\nReservation Details:")
                print(f"ID: {reservation['id']}")
                print(f"Guest: {reservation['guest_name']}")
                print(f"Room: {reservation['room_name']}")
                print(f"Dates: {format_date(reservation['start_date'])} - {format_date(reservation['end_date'])}")
                print(f"Number of Guests: {reservation['num_guests']}")
                print(f"Status: {reservation['status']}")
                if reservation.get('special_requests'):
                    print(f"Special Requests: {reservation['special_requests']}")
            except Exception as e:
                print(f"Error: {str(e)}")
                
        elif choice == "3":
            res_id = input("Enter reservation ID to cancel: ")
            if not res_id.isdigit():
                print("Invalid reservation ID")
                continue
                
            try:
                api_client.cancel_reservation(int(res_id))
                print("Reservation cancelled successfully")
            except Exception as e:
                print(f"Error: {str(e)}")
                
        elif choice == "4":
            # Find guest first
            search_term = input("Enter guest name, email, or phone: ")
            if not search_term:
                continue
                
            try:
                guests = api_client.find_guests(name=search_term)
                if not guests:
                    print("No guests found")
                    continue
                    
                print("\nFound guests:")
                for i, guest in enumerate(guests, 1):
                    print(f"{i}. {guest['name']} (ID: {guest['id']})")
                    
                selection = input("\nSelect guest number: ")
                if not selection.isdigit() or not 1 <= int(selection) <= len(guests):
                    print("Invalid selection")
                    continue
                    
                guest_id = guests[int(selection)-1]['id']
                include_cancelled = input("Include cancelled reservations? (y/n): ").lower() == 'y'
                
                reservations = api_client.get_guest_reservations(guest_id, include_cancelled)
                if not reservations:
                    print("No reservations found")
                    continue
                    
                print("\nReservations:")
                for res in reservations:
                    print(f"\nID: {res['id']}")
                    print(f"Room: {res['room_name']}")
                    print(f"Dates: {format_date(res['start_date'])} - {format_date(res['end_date'])}")
                    print(f"Status: {res['status']}")
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                
        elif choice == "5":
            # Get room first
            properties = api_client.list_properties()
            if not properties:
                print("No properties available.")
                continue
                
            print("\nSelect Property:")
            for i, prop in enumerate(properties, 1):
                print(f"{i}. {prop['name']}")
                
            prop_choice = input("\nEnter property number: ")
            if not prop_choice.isdigit() or not 1 <= int(prop_choice) <= len(properties):
                print("Invalid selection")
                continue
                
            property_id = properties[int(prop_choice)-1]['id']
            property_data = api_client.get_property(property_id)
            
            if not property_data.get('buildings'):
                print("No buildings in this property")
                continue
                
            rooms = []
            for building in property_data['buildings']:
                if building.get('rooms'):
                    for room in building['rooms']:
                        rooms.append({
                            'id': room['id'],
                            'name': f"{building['name']} - Room {room['room_number']} ({room['name']})"
                        })
            
            if not rooms:
                print("No rooms found")
                continue
                
            print("\nSelect Room:")
            for i, room in enumerate(rooms, 1):
                print(f"{i}. {room['name']}")
                
            room_choice = input("\nEnter room number: ")
            if not room_choice.isdigit() or not 1 <= int(room_choice) <= len(rooms):
                print("Invalid selection")
                continue
                
            room_id = rooms[int(room_choice)-1]['id']
            
            # Get dates
            start_date = get_date_input("Enter start date (YYYY-MM-DD): ")
            if not start_date:
                continue
                
            end_date = get_date_input("Enter end date (YYYY-MM-DD): ")
            if not end_date:
                continue
            
            try:
                availability = api_client.check_room_availability(room_id, start_date, end_date)
                if availability['available']:
                    print("\n✅ Room is available for these dates")
                else:
                    print("\n❌ Room is not available for these dates")
                    if availability.get('conflicts'):
                        print("\nConflicting reservations:")
                        for res in availability['conflicts']:
                            print(f"- {format_date(res['start_date'])} to {format_date(res['end_date'])}")
            except Exception as e:
                print(f"Error: {str(e)}")
                
        elif choice == "6":
            properties = api_client.list_properties()
            if not properties:
                print("No properties available.")
                continue
                
            print("\nSelect Property:")
            for i, prop in enumerate(properties, 1):
                print(f"{i}. {prop['name']}")
                
            prop_choice = input("\nEnter property number: ")
            if not prop_choice.isdigit() or not 1 <= int(prop_choice) <= len(properties):
                print("Invalid selection")
                continue
                
            property_id = properties[int(prop_choice)-1]['id']
            
            # Get dates
            start_date = get_date_input("Enter start date (YYYY-MM-DD): ")
            if not start_date:
                continue
                
            end_date = get_date_input("Enter end date (YYYY-MM-DD): ")
            if not end_date:
                continue
            
            try:
                availability = api_client.get_property_availability(property_id, start_date, end_date)
                print(f"\nAvailability Report for {format_date(start_date)} to {format_date(end_date)}")
                print(f"Total Rooms: {availability['total_rooms']}")
                print(f"Available Rooms: {len(availability['available_rooms'])}")
                
                if availability['available_rooms']:
                    print("\nAvailable Rooms:")
                    for room in availability['available_rooms']:
                        print(f"- Room {room['room_number']} - {room['name']}")
                        
                if availability.get('occupied_rooms'):
                    print("\nOccupied Rooms:")
                    for room in availability['occupied_rooms']:
                        print(f"- Room {room['room_number']} - {room['name']}")
                        if room.get('reservations'):
                            for res in room['reservations']:
                                print(f"  • {format_date(res['start_date'])} to {format_date(res['end_date'])} ({res['guest_name']})")
            except Exception as e:
                print(f"Error: {str(e)}")
                
        elif choice == "7":
            date_str = get_date_input("Enter date for report (YYYY-MM-DD) or press Enter for today: ")
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            try:
                report = api_client.get_daily_report(date_str)
                print(f"\nDaily Occupancy Report for {format_date(date_str)}")
                print(f"Total Rooms: {report['total_rooms']}")
                print(f"Occupied Rooms: {report['occupied_rooms']}")
                print(f"Occupancy Rate: {report['occupancy_rate']:.1f}%")
                
                if report.get('check_ins'):
                    print("\nCheck-ins Today:")
                    for res in report['check_ins']:
                        print(f"- Room {res['room_number']}: {res['guest_name']} ({res['reservation_id']})")
                        
                if report.get('check_outs'):
                    print("\nCheck-outs Today:")
                    for res in report['check_outs']:
                        print(f"- Room {res['room_number']}: {res['guest_name']} ({res['reservation_id']})")
                        
                if report.get('staying'):
                    print("\nCurrent Guests:")
                    for res in report['staying']:
                        print(f"- Room {res['room_number']}: {res['guest_name']} (until {format_date(res['end_date'])})")
            except Exception as e:
                print(f"Error: {str(e)}")
                
        elif choice == "8":
            break

def main():
    parser = argparse.ArgumentParser(description='Ressy Property Management System')
    parser.add_argument('--private-server', action='store_true', 
                      help='Use a private API server instance')
    parser.add_argument('--manage-server', action='store_true',
                      help='Show server management options in the menu')
    args = parser.parse_args()
    
    with managed_api_server(private=args.private_server) as server:
        api_client = ApiClient(base_url=server.base_url)
        
        while True:
            server_status = server.get_status()
            print("\nRessy Management System")
            print(server_status)
            print("\n1. Manage Properties")
            print("2. Manage Guests")
            print("3. Manage Reservations")
            print("4. Wipe Database")
            if args.manage_server:
                print("5. Start API Server")
                print("6. Stop API Server")
                print("7. Exit")
            else:
                print("5. Exit")
            
            max_choice = 7 if args.manage_server else 5
            choice = input(f"\nEnter your choice (1-{max_choice}) or press Enter to go back: ")
            
            if not choice:
                continue
                
            if choice == "1":
                if not server.check_server():
                    print("API Server is not running. Please start it first.")
                    continue
                manage_properties(api_client)
            elif choice == "2":
                if not server.check_server():
                    print("API Server is not running. Please start it first.")
                    continue
                manage_guests(api_client)
            elif choice == "3":
                if not server.check_server():
                    print("API Server is not running. Please start it first.")
                    continue
                manage_reservations(api_client)
            elif choice == "4":
                confirm = input("WARNING: This will delete all data from the database. Are you sure? (type 'YES' to confirm): ")
                if confirm == "YES":
                    try:
                        Base.metadata.drop_all(engine)
                        Base.metadata.create_all(engine)
                        print("Database has been wiped and recreated.")
                    except Exception as e:
                        print(f"Error wiping database: {str(e)}")
                else:
                    print("Database wipe cancelled.")
            elif args.manage_server and choice == "5":
                if server.start_server():
                    print("API Server started successfully")
                else:
                    print("Failed to start API Server")
            elif args.manage_server and choice == "6":
                if server.stop_server():
                    print("API Server stopped successfully")
                else:
                    print("Failed to stop API Server")
            elif (args.manage_server and choice == "7") or (not args.manage_server and choice == "5"):
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
