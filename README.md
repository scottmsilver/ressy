# Ressy - Property Management System

Ressy is a comprehensive property management system designed to help manage properties, reservations, and guests. It provides powerful features for tracking occupancy, revenue, and forecasting.

## Features

- Property and Building Management
- Room Management with Amenities
- Guest Profiles and Management
- Reservation System
- Detailed Reporting
  - Occupancy Reports
  - Revenue Reports
  - Forecasting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/scottmsilver/ressy.git
cd ressy
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python main.py
```

### Using the CLI

The system provides a command-line interface for various operations:

```bash
# Property Management
python cli.py properties create --name "Sample Property"
python cli.py buildings create <property-id> --name "Main Building"
python cli.py rooms create <building-id> --name "Room 101" --room-number "101"

# Guest Management
python cli.py guests create --name "John Doe" --email "john@example.com" --phone "+1234567890"

# Reservations
python cli.py reservations create --room-id <room-id> --guest-id <guest-id> --start-date "2024-01-01" --end-date "2024-01-05"

# Reports
python cli.py reports summary <property-id> --start-date "2024-01-01" --end-date "2024-01-31"
python cli.py reports revenue <property-id> --start-date "2024-01-01" --end-date "2024-01-31"
python cli.py reports occupancy <property-id> --start-date "2024-01-01" --end-date "2024-01-31"
python cli.py reports forecast <property-id> --start-date "2024-01-01" --end-date "2024-01-31"
```

## Development

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
