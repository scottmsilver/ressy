#!/usr/bin/env python3

import click
import requests
from datetime import datetime, date
from typing import Optional, Union, List, Dict, Any
import json
from tabulate import tabulate

API_URL = "http://localhost:8000"

def format_response(response: Union[List[Dict[str, Any]], Dict[str, Any]], table_format=True) -> str:
    """Format API response for CLI output"""
    if not table_format:
        return json.dumps(response, indent=2)
    
    if not response:
        return "No items found"
    
    if hasattr(response, '__iter__') and not isinstance(response, dict):
        if not response:
            return "No items found"
        headers = response[0].keys()
        rows = [[str(item.get(h, '')) for h in headers] for item in response]
        return tabulate(rows, headers=headers, tablefmt="grid")
    else:
        rows = [[k, str(v)] for k, v in response.items()]
        return tabulate(rows, headers=["Field", "Value"], tablefmt="grid")

@click.group()
def cli():
    """Ressy - Property Management System CLI"""
    pass

# Guest Management Commands
@cli.group()
def guests():
    """Guest management commands"""
    pass

@guests.command()
@click.option('--name', required=True, help='Guest name')
@click.option('--email', help='Guest email')
@click.option('--phone', help='Guest phone')
@click.option('--preferences', help='Guest preferences as JSON string')
@click.option('--contact-emails', help='Comma-separated list of additional contact emails')
@click.option('--family-id', type=int, help='Family ID to associate with')
@click.option('--override/--no-override', default=False, help='Override if guest exists')
def create(name, email, phone, preferences, contact_emails, family_id, override):
    """Create a new guest"""
    if not email and not phone:
        click.echo("Error: At least one contact method (email or phone) is required")
        return
    
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "override_duplicate": override,
        "family_id": family_id
    }
    
    if preferences:
        try:
            data["preferences"] = json.loads(preferences)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON format for preferences")
            return
    
    if contact_emails:
        data["contact_emails"] = [e.strip() for e in contact_emails.split(',')]
    
    response = requests.post(f"{API_URL}/guests/", json=data)
    if response.status_code == 200:
        click.echo("Guest created successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@guests.command()
@click.option('--name', help='Search by name')
@click.option('--email', help='Search by email')
@click.option('--phone', help='Search by phone')
def find(name, email, phone):
    """Find guests by name, email, or phone"""
    params = {}
    if name:
        params['name'] = name
    if email:
        params['email'] = email
    if phone:
        params['phone'] = phone
    
    response = requests.get(f"{API_URL}/guests/", params=params)
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@guests.command()
@click.argument('guest_id', type=int)
def get(guest_id):
    """Get guest details by ID"""
    response = requests.get(f"{API_URL}/guests/{guest_id}")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@guests.command()
@click.argument('guest_id', type=int)
@click.option('--preferences', required=True, help='Guest preferences as JSON string')
def update_preferences(guest_id, preferences):
    """Update guest preferences"""
    try:
        prefs_data = json.loads(preferences)
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON format for preferences")
        return
    
    response = requests.put(f"{API_URL}/guests/{guest_id}/preferences", json=prefs_data)
    if response.status_code == 200:
        click.echo("Preferences updated successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@guests.command()
@click.argument('guest_id', type=int)
@click.option('--email', required=True, help='New contact email to add')
def add_contact_email(guest_id, email):
    """Add a contact email to a guest"""
    response = requests.post(f"{API_URL}/guests/{guest_id}/contact-emails", json={"email": email})
    if response.status_code == 200:
        click.echo("Contact email added successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@guests.command()
@click.argument('primary_guest_id', type=int)
@click.argument('secondary_guest_id', type=int)
def merge(primary_guest_id, secondary_guest_id):
    """Merge two guest records, keeping the primary guest and deleting the secondary"""
    response = requests.post(f"{API_URL}/guests/{primary_guest_id}/merge/{secondary_guest_id}")
    if response.status_code == 200:
        click.echo("Guests merged successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@guests.command()
@click.argument('guest_id', type=int)
def get_family(guest_id):
    """Get family details for a guest"""
    response = requests.get(f"{API_URL}/guests/{guest_id}/family")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@guests.command()
@click.argument('guest_id', type=int)
def get_reservations(guest_id):
    """Get all reservations for a guest"""
    response = requests.get(f"{API_URL}/guests/{guest_id}/reservations")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

# Family Management Commands
@cli.group()
def families():
    """Family management commands"""
    pass

@families.command()
@click.option('--name', required=True, help='Family name')
@click.option('--primary-contact-id', type=int, help='Primary contact guest ID')
def create(name, primary_contact_id):
    """Create a new family"""
    data = {
        "name": name,
        "primary_contact_id": primary_contact_id
    }
    
    response = requests.post(f"{API_URL}/families/", json=data)
    if response.status_code == 200:
        click.echo("Family created successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@families.command()
@click.argument('family_id', type=int)
@click.argument('guest_id', type=int)
def add_member(family_id, guest_id):
    """Add a guest to a family"""
    response = requests.post(f"{API_URL}/families/{family_id}/members/{guest_id}")
    if response.status_code == 200:
        click.echo("Family member added successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@families.command()
@click.argument('family_id', type=int)
def members(family_id):
    """List family members"""
    response = requests.get(f"{API_URL}/families/{family_id}/members")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

# Property Management Commands
@cli.group()
def properties():
    """Property management commands"""
    pass

@properties.command()
@click.option('--name', required=True, help='Property name')
@click.option('--address', required=True, help='Property address')
def create(name, address):
    """Create a new property"""
    data = {
        "name": name,
        "address": address
    }
    
    response = requests.post(f"{API_URL}/properties/", json=data)
    if response.status_code == 200:
        click.echo("Property created successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@properties.command()
@click.option('--name', help='Filter by name')
@click.option('--address', help='Filter by address')
def list(name, address):
    """List properties"""
    params = {}
    if name:
        params['name'] = name
    if address:
        params['address'] = address
    
    response = requests.get(f"{API_URL}/properties/", params=params)
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

# Building Management Commands
@cli.group()
def buildings():
    """Building management commands"""
    pass

@buildings.command()
@click.argument('property_id', type=int)
@click.option('--name', required=True, help='Building name')
def create(property_id, name):
    """Create a new building"""
    data = {"name": name}
    
    response = requests.post(f"{API_URL}/properties/{property_id}/buildings/", json=data)
    if response.status_code == 200:
        click.echo("Building created successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@buildings.command()
@click.argument('property_id', type=int)
def list(property_id):
    """List buildings in a property"""
    response = requests.get(f"{API_URL}/properties/{property_id}/buildings/")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

# Room Management Commands
@cli.group()
def rooms():
    """Room management commands"""
    pass

@rooms.command()
@click.argument('building_id', type=int)
@click.option('--name', required=True, help='Room name')
@click.option('--room-number', required=True, help='Room number')
@click.option('--amenities', help='Comma-separated list of amenities')
def create(building_id, name, room_number, amenities):
    """Create a new room"""
    data = {
        "name": name,
        "room_number": room_number,
        "amenities": amenities.split(',') if amenities else []
    }
    
    response = requests.post(f"{API_URL}/buildings/{building_id}/rooms/", json=data)
    if response.status_code == 200:
        click.echo("Room created successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@rooms.command()
@click.argument('building_id', type=int)
def list(building_id):
    """List rooms in a building"""
    response = requests.get(f"{API_URL}/buildings/{building_id}/rooms/")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@rooms.command()
@click.argument('room_id', type=int)
@click.option('--start-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='End date (YYYY-MM-DD)')
def check_availability(room_id, start_date, end_date):
    """Check room availability for a date range"""
    params = {
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat()
    }
    
    response = requests.get(f"{API_URL}/rooms/{room_id}/availability", params=params)
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

# Bed Management Commands
@cli.group()
def beds():
    """Bed management commands"""
    pass

@beds.command()
@click.argument('room_id', type=int)
@click.option('--bed-type', required=True, type=click.Choice(['single', 'double', 'queen', 'king']), help='Bed type')
@click.option('--bed-subtype', required=True, type=click.Choice(['standard', 'sofa', 'bunk']), help='Bed subtype')
def create(room_id, bed_type, bed_subtype):
    """Add a bed to a room"""
    data = {
        "bed_type": bed_type,
        "bed_subtype": bed_subtype
    }
    
    response = requests.post(f"{API_URL}/rooms/{room_id}/beds/", json=data)
    if response.status_code == 200:
        click.echo("Bed added successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@beds.command()
@click.argument('room_id', type=int)
def list(room_id):
    """List beds in a room"""
    response = requests.get(f"{API_URL}/rooms/{room_id}/beds/")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

# Reservation Management Commands
@cli.group()
def reservations():
    """Reservation management commands"""
    pass

@reservations.command()
@click.option('--guest-id', required=True, type=int, help='Guest ID')
@click.option('--room-id', required=True, type=int, help='Room ID')
@click.option('--start-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='End date (YYYY-MM-DD)')
@click.option('--num-guests', default=1, type=int, help='Number of guests')
@click.option('--special-requests', help='Special requests')
def create(guest_id, room_id, start_date, end_date, num_guests, special_requests):
    """Create a new reservation"""
    data = {
        "guest_id": guest_id,
        "room_id": room_id,
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(),
        "num_guests": num_guests,
        "special_requests": special_requests
    }
    
    response = requests.post(f"{API_URL}/reservations/", json=data)
    if response.status_code == 200:
        click.echo("Reservation created successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@reservations.command()
@click.argument('reservation_id', type=int)
def get(reservation_id):
    """Get reservation details"""
    response = requests.get(f"{API_URL}/reservations/{reservation_id}")
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@reservations.command()
@click.argument('reservation_id', type=int)
def cancel(reservation_id):
    """Cancel a reservation"""
    response = requests.post(f"{API_URL}/reservations/{reservation_id}/cancel")
    if response.status_code == 200:
        click.echo("Reservation cancelled successfully:")
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@reservations.command()
@click.option('--guest-id', type=int, help='Filter by guest ID')
@click.option('--room-id', type=int, help='Filter by room ID')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Filter by start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Filter by end date (YYYY-MM-DD)')
@click.option('--status', type=click.Choice(['confirmed', 'cancelled']), help='Filter by status')
def list(guest_id, room_id, start_date, end_date, status):
    """List reservations with optional filters"""
    params = {}
    if guest_id:
        params['guest_id'] = guest_id
    if room_id:
        params['room_id'] = room_id
    if start_date:
        params['start_date'] = start_date.date().isoformat()
    if end_date:
        params['end_date'] = end_date.date().isoformat()
    if status:
        params['status'] = status
    
    response = requests.get(f"{API_URL}/reservations/", params=params)
    if response.status_code == 200:
        click.echo(format_response(response.json()))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@reservations.command()
@click.argument('room_id', type=int)
@click.option('--start-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='End date (YYYY-MM-DD)')
def check_availability(room_id, start_date, end_date):
    """Check room availability for a date range"""
    params = {
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat()
    }
    
    response = requests.get(f"{API_URL}/rooms/{room_id}/availability", params=params)
    if response.status_code == 200:
        result = response.json()
        if result["available"]:
            click.echo("Room is available for the specified dates")
        else:
            click.echo("Room is not available. Conflicts:")
            click.echo(format_response(result["conflicts"]))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@reservations.command()
@click.argument('property_id', type=int)
@click.option('--start-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='End date (YYYY-MM-DD)')
def property_availability(property_id, start_date, end_date):
    """Get availability report for an entire property"""
    params = {
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat()
    }
    
    response = requests.get(f"{API_URL}/properties/{property_id}/availability", params=params)
    if response.status_code == 200:
        result = response.json()
        click.echo(f"Total rooms: {result['total_rooms']}")
        click.echo("\nAvailable rooms:")
        click.echo(format_response(result["available_rooms"]))
        if result.get("occupied_rooms"):
            click.echo("\nOccupied rooms:")
            click.echo(format_response(result["occupied_rooms"]))
    else:
        click.echo(f"Error: {response.json()['detail']}")

@reservations.command()
@click.option('--date', required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help='Report date (YYYY-MM-DD)')
def daily_report(date):
    """Get daily occupancy report"""
    response = requests.get(f"{API_URL}/reports/daily/{date.date().isoformat()}")
    if response.status_code == 200:
        result = response.json()
        click.echo(f"Daily Report for {date.date().isoformat()}")
        click.echo(f"Total rooms: {result['total_rooms']}")
        click.echo(f"Occupied rooms: {result['occupied_rooms']}")
        click.echo(f"Occupancy rate: {result['occupancy_rate']}%")
        
        if result.get("check_ins"):
            click.echo("\nCheck-ins today:")
            click.echo(format_response(result["check_ins"]))
        
        if result.get("check_outs"):
            click.echo("\nCheck-outs today:")
            click.echo(format_response(result["check_outs"]))
        
        if result.get("staying"):
            click.echo("\nCurrently staying:")
            click.echo(format_response(result["staying"]))
    else:
        click.echo(f"Error: {response.json()['detail']}")

# Reporting Commands
@cli.group()
def reports():
    """Property reporting commands"""
    pass

@reports.command()
@click.argument('property_id', type=int)
@click.option('--start-date', required=True, type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=str, help='End date (YYYY-MM-DD)')
def summary(property_id, start_date, end_date):
    """Get a comprehensive property report"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        params = {
            "start_date": start.isoformat(),
            "end_date": end.isoformat()
        }
        
        click.echo(f"Fetching property report for property {property_id}...")
        response = requests.get(f"{API_URL}/properties/{property_id}/reports/summary", params=params)
        
        if response.status_code == 200:
            result = response.json()
            click.echo(f"\nProperty Summary Report ({start_date} to {end_date})")
            click.echo(f"Total Rooms: {result['total_rooms']}")
            click.echo(f"Occupied Rooms: {result['occupied_rooms']}")
            click.echo(f"Occupancy Rate: {result['occupancy_rate']:.2f}%")
            click.echo(f"Total Revenue: ${result['revenue']:,.2f}")
            click.echo(f"Average Daily Rate: ${result['avg_daily_rate']:,.2f}")
            
            click.echo("\nBuilding Details:")
            for building in result['buildings']:
                click.echo(f"\n{building['name']}:")
                click.echo(f"  Total Rooms: {building['total_rooms']}")
                click.echo(f"  Occupied Rooms: {building['occupied_rooms']}")
                click.echo(f"  Occupancy Rate: {building['occupancy_rate']:.2f}%")
                click.echo(f"  Revenue: ${building['revenue']:,.2f}")
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            click.echo(f"Error: {error_detail}")
    except ValueError as e:
        click.echo(f"Error: Invalid date format. Please use YYYY-MM-DD")
    except requests.RequestException as e:
        click.echo(f"Error: Failed to connect to API: {str(e)}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@reports.command()
@click.argument('property_id', type=int)
@click.option('--start-date', required=True, type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=str, help='End date (YYYY-MM-DD)')
def revenue(property_id, start_date, end_date):
    """Get a detailed revenue report"""
    click.echo(f"\nFetching revenue report for property {property_id}...")
    
    try:
        response = requests.get(f"{API_URL}/properties/{property_id}/reports/revenue?start_date={start_date}&end_date={end_date}")
        result = response.json()
        
        click.echo(f"\nRevenue Report ({start_date} to {end_date})")
        click.echo(f"Total Revenue: ${result['total_revenue']:,.2f}")
        click.echo(f"Total Bookings: {result['total_bookings']}")
        click.echo("\nRevenue by Date:")
        click.echo("Date           Revenue    Bookings")
        click.echo("-" * 40)
        
        for day in result['revenue_by_date']:
            click.echo(f"{day['date']}  ${day['revenue']:8,.2f}  {day['bookings']:8d}")
            
    except requests.RequestException as e:
        if hasattr(e.response, 'json'):
            click.echo(f"Error: {e.response.json()['detail']}")
        else:
            click.echo(f"Error: {str(e)}")

@reports.command()
@click.argument('property_id', type=int)
@click.option('--start-date', required=True, type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=str, help='End date (YYYY-MM-DD)')
def occupancy(property_id, start_date, end_date):
    """Get a detailed occupancy report"""
    click.echo(f"\nFetching occupancy report for property {property_id}...")
    
    try:
        response = requests.get(f"{API_URL}/properties/{property_id}/reports/occupancy?start_date={start_date}&end_date={end_date}")
        result = response.json()
        
        click.echo(f"\nOccupancy Report ({start_date} to {end_date})")
        click.echo(f"Total Rooms: {result['total_rooms']}")
        click.echo(f"Average Occupancy Rate: {result['avg_occupancy_rate']:.2f}%")
        
        click.echo("\nDaily Occupancy:")
        click.echo("Date           Occupied  Total    Rate")
        click.echo("-" * 45)
        
        for day in result['occupancy_by_date']:
            click.echo(f"{day['date']}  {day['occupied_rooms']:8d}  {day['total_rooms']:8d}  {day['occupancy_rate']:6.2f}%")
            
    except requests.RequestException as e:
        if hasattr(e.response, 'json'):
            click.echo(f"Error: {e.response.json()['detail']}")
        else:
            click.echo(f"Error: {str(e)}")

@reports.command()
@click.argument('property_id', type=int)
@click.option('--start-date', required=True, type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, type=str, help='End date (YYYY-MM-DD)')
def forecast(property_id, start_date, end_date):
    """Get a forecast report"""
    click.echo(f"\nFetching forecast report for property {property_id}...")
    
    try:
        response = requests.get(f"{API_URL}/properties/{property_id}/reports/forecast?start_date={start_date}&end_date={end_date}")
        result = response.json()
        
        click.echo(f"\nForecast Report ({start_date} to {end_date})")
        click.echo(f"Total Predicted Revenue: ${result['total_predicted_revenue']:,.2f}")
        click.echo(f"Average Predicted Occupancy Rate: {result['avg_predicted_occupancy']:.2f}%")
        
        click.echo("\nDaily Forecast:")
        click.echo("Date           Occupancy  Revenue   Confidence")
        click.echo("-" * 50)
        
        for day in result['forecast_by_date']:
            click.echo(f"{day['date']}  {day['predicted_occupancy']:8.2f}%  ${day['predicted_revenue']:8,.2f}  {day['confidence']:8.2f}%")
            
    except requests.RequestException as e:
        if hasattr(e.response, 'json'):
            click.echo(f"Error: {e.response.json()['detail']}")
        else:
            click.echo(f"Error: {str(e)}")

if __name__ == '__main__':
    cli()
