import {
  Property, Building, Room, Bed, Guest, Reservation,
  CreatePropertyRequest, CreateBuildingRequest, CreateRoomRequest,
  CreateBedRequest, CreateGuestRequest, CreateReservationRequest,
  RoomAvailabilityResponse, ApiError, UpdateRoomRequest
} from './types';

export interface PropertyReservation {
  room_id: number;
  room_name: string;
  room_number: string;
  building_id: number;
  building_name: string;
  guest_id: number;
  guest_name: string;
  start_date: string;
  end_date: string;
  status: string;
}

export interface PropertyReservationsResponse {
  total_rooms: number;
  reservations: PropertyReservation[];
}

export class RessyApi {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000/api') {
    this.baseURL = baseURL;
  }

  // Health check
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      console.log('Health check response:', data);
      return data && typeof data === 'object' && 'status' in data && data.status === 'ok';
    } catch (error) {
      console.error('Health check error:', error);
      return false;
    }
  }

  // Property methods
  async createProperty(data: CreatePropertyRequest): Promise<Property> {
    try {
      const response = await fetch(`${this.baseURL}/properties`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Create property error:', error);
      throw error;
    }
  }

  async getProperty(id: number): Promise<Property> {
    try {
      const response = await fetch(`${this.baseURL}/properties/${id}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('API Response:', JSON.stringify(data, null, 2));
      
      // Ensure the response matches our expected structure
      if (!data.buildings) {
        console.error('API Response missing buildings array:', data);
        throw new Error('Invalid API response: missing buildings array');
      }
      
      // Initialize empty arrays if they don't exist
      const property: Property = {
        ...data,
        buildings: data.buildings.map((building: Building) => ({
          ...building,
          rooms: building.rooms?.map((room: Room) => ({
            ...room,
            beds: room.beds || [],
            amenities: room.amenities || [],
          })) || [],
        })),
      };
      
      return property;
    } catch (error) {
      console.error('Get property error:', error);
      throw error;
    }
  }

  async listProperties(): Promise<Property[]> {
    try {
      const response = await fetch(`${this.baseURL}/properties`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('List properties error:', error);
      throw error;
    }
  }

  async deleteProperty(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/properties/${id}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Delete property error:', error);
      throw error;
    }
  }

  async updateProperty(id: number, data: { name?: string; address?: string }): Promise<Property> {
    try {
      const response = await fetch(`${this.baseURL}/properties/${id}`, {
        method: 'PUT',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Update property error:', error);
      throw error;
    }
  }

  async getPropertyReservations(
    propertyId: number,
    startDate: string,
    endDate: string
  ): Promise<PropertyReservationsResponse> {
    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });

      const response = await fetch(
        `${this.baseURL}/properties/${propertyId}/reservations?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        }
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Get property reservations error:', error);
      throw error;
    }
  }

  // Building methods
  async createBuilding(propertyId: number, data: CreateBuildingRequest): Promise<Building> {
    try {
      const response = await fetch(`${this.baseURL}/properties/${propertyId}/buildings`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Create building error:', error);
      throw error;
    }
  }

  async listBuildings(propertyId: number): Promise<Building[]> {
    try {
      const response = await fetch(`${this.baseURL}/properties/${propertyId}/buildings`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('List buildings error:', error);
      throw error;
    }
  }

  async deleteBuilding(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/buildings/${id}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Delete building error:', error);
      throw error;
    }
  }

  async updateBuilding(id: number, data: { name: string }): Promise<Building> {
    try {
      const response = await fetch(`${this.baseURL}/buildings/${id}`, {
        method: 'PUT',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Update building error:', error);
      throw error;
    }
  }

  // Room methods
  async createRoom(buildingId: number, data: CreateRoomRequest): Promise<Room> {
    try {
      const response = await fetch(`${this.baseURL}/buildings/${buildingId}/rooms`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Create room error:', error);
      throw error;
    }
  }

  async listRooms(buildingId: number): Promise<Room[]> {
    try {
      const response = await fetch(`${this.baseURL}/buildings/${buildingId}/rooms`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('List rooms error:', error);
      throw error;
    }
  }

  async deleteRoom(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/rooms/${id}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Delete room error:', error);
      throw error;
    }
  }

  async updateRoom(roomId: number, update: UpdateRoomRequest): Promise<Room> {
    const response = await fetch(`${this.baseURL}/rooms/${roomId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(update),
    });

    if (!response.ok) {
      throw new Error(`Failed to update room: ${response.statusText}`);
    }

    return response.json();
  }

  async checkRoomAvailability(roomId: number, startDate: string, endDate: string): Promise<RoomAvailabilityResponse> {
    try {
      const response = await fetch(`${this.baseURL}/rooms/${roomId}/availability?start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Check room availability error:', error);
      throw error;
    }
  }

  async createBed(roomId: number, data: CreateBedRequest): Promise<Bed> {
    try {
      console.log('Creating bed:', { roomId, data });
      const response = await fetch(`${this.baseURL}/rooms/${roomId}/beds`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          bed_type: data.type,
          bed_subtype: data.subtype
        }),
      });
      
      const responseText = await response.text();
      console.log('API Response:', responseText);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}, response: ${responseText}`);
      }
      
      try {
        const bed = JSON.parse(responseText);
        console.log('Created bed:', bed);
        return bed;
      } catch (e) {
        console.error('Failed to parse bed response:', e);
        throw new Error('Invalid JSON response from server');
      }
    } catch (error) {
      console.error('Create bed error:', error);
      throw error;
    }
  }

  async listBeds(roomId: number): Promise<Bed[]> {
    try {
      const response = await fetch(`${this.baseURL}/rooms/${roomId}/beds/`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('List beds error:', error);
      throw error;
    }
  }

  async deleteBed(bedId: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/beds/${bedId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Delete bed error:', error);
      throw error;
    }
  }

  // Guest methods
  async createGuest(data: CreateGuestRequest): Promise<Guest> {
    try {
      const response = await fetch(`${this.baseURL}/guests`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Create guest error:', error);
      throw error;
    }
  }

  async getGuest(id: number): Promise<Guest> {
    try {
      const response = await fetch(`${this.baseURL}/guests/${id}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Get guest error:', error);
      throw error;
    }
  }

  async searchGuests(query: { name?: string; email?: string; phone?: string }): Promise<Guest[]> {
    try {
      const params = new URLSearchParams();
      if (query.name) params.append('name', query.name);
      if (query.email) params.append('email', query.email);
      if (query.phone) params.append('phone', query.phone);

      const response = await fetch(`${this.baseURL}/guests/?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Search guests error:', error);
      throw error;
    }
  }

  // Reservation methods
  async createReservation(data: CreateReservationRequest): Promise<Reservation> {
    try {
      const response = await fetch(`${this.baseURL}/reservations`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail || 
          (Array.isArray(errorData) ? errorData.map(e => e.msg).join(', ') : 'Failed to create reservation');
        throw new Error(errorMessage);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Create reservation error:', error);
      throw error;
    }
  }

  async getReservation(id: number): Promise<Reservation> {
    try {
      const response = await fetch(`${this.baseURL}/reservations/${id}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Get reservation error:', error);
      throw error;
    }
  }

  async cancelReservation(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/reservations/${id}/cancel`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Cancel reservation error:', error);
      throw error;
    }
  }
}
