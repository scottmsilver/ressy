import pytest
from unittest.mock import patch, MagicMock
import sys
from main import main, ApiClient, managed_api_server

@patch('sys.argv', ['main.py'])
def test_manage_properties():
    # Mock API client responses
    mock_api_client = MagicMock()
    mock_api_client.list_properties.return_value = [{
        'id': 1,
        'name': 'Test Property',
        'address': '123 Test St',
        'buildings': [{
            'id': 1,
            'name': 'Building 1',
            'rooms': [{
                'id': 1,
                'name': 'Room 101',
                'room_number': '101',
                'capacity': 2
            }]
        }]
    }]
    mock_api_client.list_buildings.return_value = [{
        'id': 1,
        'name': 'Building 1',
        'rooms': [{
            'id': 1,
            'name': 'Room 101',
            'room_number': '101',
            'capacity': 2
        }]
    }]

    # Mock user inputs for:
    # 1. Choose "Manage Properties" (1)
    # 2. List Properties (2)
    # 3. Back to Main Menu (6)
    # 4. Exit Main Menu (5)
    user_inputs = ['1', '2', '6', '5']

    with patch('builtins.input', side_effect=user_inputs):
        with patch('main.ApiClient', return_value=mock_api_client):
            with patch('main.managed_api_server') as mock_server:
                mock_server.return_value.__enter__.return_value.base_url = 'http://test'
                main()

    # Verify the API client calls
    mock_api_client.list_properties.assert_called()

@patch('sys.argv', ['main.py'])
def test_create_and_list_property():
    mock_api_client = MagicMock()
    
    # Mock successful property creation
    property_data = {
        'id': 1,
        'name': 'New Property',
        'address': '456 New St',
        'buildings': []
    }
    mock_api_client.create_property.return_value = property_data
    mock_api_client.list_properties.return_value = [property_data]

    # User inputs to:
    # 1. Choose "Manage Properties" (1)
    # 2. Create Property (1)
    # 3. Enter property name
    # 4. Enter property address
    # 5. Manage now? (n)
    # 6. List Properties (2)
    # 7. Back to Main Menu (6)
    # 8. Exit Main Menu (5)
    user_inputs = [
        '1',           # Main menu - Manage Properties
        '1',           # Property menu - Create Property
        'New Property',  # Property name
        '456 New St',    # Property address
        'n',            # Don't manage now
        '2',           # List properties
        '6',           # Back to main menu
        '5'            # Exit main menu
    ]

    with patch('builtins.input', side_effect=user_inputs):
        with patch('main.ApiClient', return_value=mock_api_client):
            with patch('main.managed_api_server') as mock_server:
                mock_server.return_value.__enter__.return_value.base_url = 'http://test'
                main()

    # Verify the API calls
    mock_api_client.create_property.assert_called_once_with('New Property', '456 New St')
    mock_api_client.list_properties.assert_called()

@patch('sys.argv', ['main.py'])
def test_create_property_building_room_bed():
    mock_api_client = MagicMock()

    # Mock responses
    property_data = {
        'id': 1,
        'name': 'Seaside Resort',
        'address': '789 Ocean Drive',
        'buildings': []
    }
    mock_api_client.create_property.return_value = property_data
    mock_api_client.list_properties.return_value = [property_data]

    building_data = {
        'id': 1,
        'name': 'Ocean Wing',
        'property_id': 1,
        'rooms': []
    }
    mock_api_client.create_building.return_value = building_data
    mock_api_client.list_buildings.return_value = [building_data]

    room_data = {
        'id': 1,
        'name': 'Ocean View Suite',
        'room_number': '101',
        'building_id': 1,
        'capacity': 2,
        'amenities': []
    }
    mock_api_client.create_room.return_value = room_data
    mock_api_client.list_rooms.return_value = [room_data]

    bed_data = {
        'id': 1,
        'bed_type': 'KING',
        'bed_subtype': 'REGULAR',
        'room_id': 1,
        'capacity': 2
    }
    mock_api_client.create_bed.return_value = bed_data
    mock_api_client.list_beds.return_value = [bed_data]

    # User inputs for complete flow
    inputs = [
        '1',               # Main menu - Manage Properties
        '1',               # Property menu - Create Property
        'Seaside Resort',  # Property name
        '789 Ocean Drive', # Property address
        'y',              # Manage now
        '1',              # Create Building
        'Ocean Wing',      # Building name
        'y',              # Manage building
        '1',              # Create Room
        'Ocean View Suite', # Room name
        '101',            # Room number
        'y',              # Add beds
        '3',              # King bed (3)
        'n',              # Not a bunk bed
        'done',           # Finish adding beds
        '6',              # Back to Room Menu
        '6',              # Back to Building Menu
        '6',              # Back to Property Menu
        '6',              # Back to Main Menu
        '5'               # Exit
    ]

    with patch('builtins.input', side_effect=inputs), \
         patch('main.ApiClient', return_value=mock_api_client), \
         patch('main.managed_api_server') as mock_server:
        mock_server.return_value.__enter__.return_value.base_url = 'http://test'
        main()

    # Verify API calls
    mock_api_client.create_property.assert_called_once_with('Seaside Resort', '789 Ocean Drive')
    mock_api_client.create_building.assert_called_once_with(1, 'Ocean Wing')
    mock_api_client.create_room.assert_called_once_with(1, 'Ocean View Suite', '101')
    mock_api_client.create_bed.assert_called_once_with(1, 'KING', 'REGULAR')

@patch('sys.argv', ['main.py'])
def test_create_full_property_chain():
    """Test creating a property with building, room and bed"""
    mock_api_client = MagicMock()
    
    # Mock responses
    mock_api_client.create_property.return_value = {
        'id': 1,
        'name': 'Seaside Resort',
        'address': '789 Ocean Drive',
        'buildings': []
    }
    mock_api_client.list_properties.return_value = [{
        'id': 1,
        'name': 'Seaside Resort',
        'address': '789 Ocean Drive',
        'buildings': []
    }]

    mock_api_client.create_building.return_value = {
        'id': 1,
        'name': 'Ocean Wing',
        'property_id': 1,
        'rooms': []
    }
    mock_api_client.list_buildings.return_value = [{
        'id': 1,
        'name': 'Ocean Wing',
        'property_id': 1,
        'rooms': []
    }]

    mock_api_client.create_room.return_value = {
        'id': 1,
        'name': 'Ocean View Suite',
        'room_number': '101',
        'building_id': 1,
        'capacity': 2,
        'amenities': []
    }
    mock_api_client.list_rooms.return_value = [{
        'id': 1,
        'name': 'Ocean View Suite',
        'room_number': '101',
        'building_id': 1,
        'capacity': 2,
        'amenities': []
    }]

    mock_api_client.create_bed.return_value = {
        'id': 1,
        'bed_type': 'KING',
        'bed_subtype': 'REGULAR',
        'room_id': 1,
        'capacity': 2
    }
    mock_api_client.list_beds.return_value = [{
        'id': 1,
        'bed_type': 'KING',
        'bed_subtype': 'REGULAR',
        'room_id': 1,
        'capacity': 2
    }]

    # Simulate user input sequence
    inputs = [
        '1',               # Main menu - Manage Properties
        '1',               # Create Property
        'Seaside Resort',  # Property name
        '789 Ocean Drive', # Property address
        'y',              # Manage now
        '1',              # Create Building
        'Ocean Wing',      # Building name
        'y',              # Manage building
        '1',              # Create Room
        'Ocean View Suite', # Room name
        '101',            # Room number
        'y',              # Add bed
        '3',              # King bed (3)
        'n',              # Not a bunk bed
        'done',           # Finish adding beds
        '6',              # Back to Room Menu
        '6',              # Back to Building Menu
        '6',              # Back to Property Menu
        '6',              # Back to Main Menu
        '5'               # Exit
    ]

    with patch('builtins.input', side_effect=inputs), \
         patch('main.ApiClient', return_value=mock_api_client), \
         patch('main.managed_api_server') as mock_server:
        mock_server.return_value.__enter__.return_value.base_url = 'http://test'
        main()

    # Verify API calls
    mock_api_client.create_property.assert_called_once_with('Seaside Resort', '789 Ocean Drive')
    mock_api_client.create_building.assert_called_once_with(1, 'Ocean Wing')
    mock_api_client.create_room.assert_called_once_with(1, 'Ocean View Suite', '101')
    mock_api_client.create_bed.assert_called_once_with(1, 'KING', 'REGULAR')

if __name__ == '__main__':
    pytest.main(['-v', 'test_main.py'])
