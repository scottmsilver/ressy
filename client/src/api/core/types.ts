// Base interfaces
export interface Entity {
  id: number;
}

export enum BedType {
  SINGLE = 'single',
  DOUBLE = 'double',
  QUEEN = 'queen',
  KING = 'king'
}

export enum BedSubType {
  STANDARD = 'standard',
  SOFA = 'sofa',
  BUNK = 'bunk',
  ROLLAWAY = 'rollaway'
}

// Core domain interfaces
export interface Bed {
  id: number;
  bed_type: BedType;
  bed_subtype: BedSubType;
  capacity: number;
}

export interface Room extends Entity {
  name: string;
  room_number: string;
  building_id: number;
  amenities: string[];
  beds: Bed[];
  capacity: number;
}

export interface Building extends Entity {
  name: string;
  property_id: number;
  rooms: Room[];
}

export interface Property extends Entity {
  name: string;
  address: string;
  buildings: Building[];
}

export interface Guest extends Entity {
  name: string;
  email?: string;
  phone?: string;
  preferences: Record<string, unknown>;
  contactEmails: string[];
  familyId?: number;
}

export interface Reservation extends Entity {
  id: number;
  guest_id: number;
  guest_name: string;
  guest_email?: string;
  guest_phone?: string;
  room_id: number;
  room_name: string;
  room_number: string;
  building_id: number;
  building_name: string;
  start_date: string;
  end_date: string;
  notes?: string;
  status: 'confirmed' | 'cancelled' | 'pending';
}

// API Request/Response types
export interface CreatePropertyRequest {
  name: string;
  address: string;
}

export interface UpdatePropertyRequest {
  name?: string;
  address?: string;
}

export interface CreateBuildingRequest {
  name: string;
}

export interface UpdateBuildingRequest {
  name: string;
}

export interface CreateRoomRequest {
  name: string;
  room_number: string;
  amenities?: string[];
}

export interface UpdateRoomRequest {
  name?: string;
  room_number?: string;
}

export interface UpdateRoomAmenitiesRequest {
  amenities: string[];
}

export interface CreateBedRequest {
  type: BedType;
  subtype: BedSubType;
}

export interface CreateGuestRequest {
  name: string;
  email?: string;
  phone?: string;
  preferences?: Record<string, unknown>;
  contactEmails?: string[];
  familyId?: number;
}

export interface CreateReservationRequest {
  guest_id: number;
  room_id: number;
  start_date: string;
  end_date: string;
  num_guests: number;
  special_requests?: string;
}

export interface RoomAvailabilityResponse {
  available: boolean;
  conflicts?: Array<{
    start_date: string;
    end_date: string;
    guest_name: string;
  }>;
}

export interface PropertyReservation {
  reservation_id: number;
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

export interface ApiError {
  status: number;
  message: string;
  details?: unknown;
}
