import { RessyApi } from './core/RessyApi';
import { BedType, BedSubType } from './core/types';

export const API_PORT = 8000;
export const api = new RessyApi(`/api`);

export {
  BedType,
  BedSubType,
}

export type {
  Property,
  Building,
  Room,
  Bed,
  Guest,
  Reservation,
  CreatePropertyRequest,
  CreateBuildingRequest,
  CreateRoomRequest,
  CreateBedRequest,
  CreateGuestRequest,
  CreateReservationRequest,
  RoomAvailabilityResponse,
  ApiError,
} from './core/types';

export { RessyApi };
