import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { RessyApi } from '../RessyApi'
import type { CreateBedRequest, CreateRoomRequest, Room, Bed } from '../types'

// Mock axios
vi.mock('axios')
const mockAxios = vi.mocked(axios)

describe('RessyApi', () => {
  let api: RessyApi
  let mockClient: any

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks()
    
    // Setup mock client
    mockClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        response: {
          use: vi.fn()
        }
      }
    }

    mockAxios.create.mockReturnValue(mockClient)
    
    // Create a new instance of RessyApi
    api = new RessyApi('/api')
  })

  describe('Health Check', () => {
    it('should return true when API is healthy', async () => {
      mockClient.get.mockResolvedValueOnce({ data: { status: 'ok' } })
      const result = await api.checkHealth()
      expect(result).toBe(true)
      expect(mockClient.get).toHaveBeenCalledWith('/health')
    })

    it('should return false when API is unhealthy', async () => {
      mockClient.get.mockRejectedValueOnce(new Error('API Error'))
      const result = await api.checkHealth()
      expect(result).toBe(false)
    })
  })

  describe('Room Management', () => {
    const mockRoom: Room = {
      id: 1,
      name: 'Test Room',
      roomNumber: '101',
      buildingId: 1,
      amenities: ['wifi', 'tv'],
      beds: [],
    }

    it('should create a room', async () => {
      const response = { data: mockRoom }
      mockClient.post.mockResolvedValueOnce(response)
      
      // Get the success interceptor function
      const successInterceptor = mockClient.interceptors.response.use.mock.calls[0][0]

      const createRoomRequest: CreateRoomRequest = {
        name: 'Test Room',
        roomNumber: '101',
        amenities: ['wifi', 'tv'],
      }

      const result = await api.createRoom(1, createRoomRequest)
      expect(successInterceptor(response)).toEqual(mockRoom)
      expect(mockClient.post).toHaveBeenCalledWith('/buildings/1/rooms', createRoomRequest)
    })

    it('should update room amenities', async () => {
      const updatedRoom = { ...mockRoom, amenities: ['wifi', 'tv', 'minibar'] }
      const response = { data: updatedRoom }
      mockClient.put.mockResolvedValueOnce(response)

      // Get the success interceptor function
      const successInterceptor = mockClient.interceptors.response.use.mock.calls[0][0]

      const newAmenities = ['wifi', 'tv', 'minibar']
      const result = await api.updateRoomAmenities(1, newAmenities)
      
      expect(successInterceptor(response)).toEqual(updatedRoom)
      expect(mockClient.put).toHaveBeenCalledWith('/rooms/1/amenities', { amenities: newAmenities })
    })
  })

  describe('Bed Management', () => {
    const mockBed: Bed = {
      id: 1,
      type: 'queen',
      subtype: 'standard',
      capacity: 2,
    }

    it('should create a bed', async () => {
      const response = { data: mockBed }
      mockClient.post.mockResolvedValueOnce(response)

      // Get the success interceptor function
      const successInterceptor = mockClient.interceptors.response.use.mock.calls[0][0]

      const createBedRequest: CreateBedRequest = {
        type: 'queen',
        subtype: 'standard',
      }

      const result = await api.createBed(1, createBedRequest)
      expect(successInterceptor(response)).toEqual(mockBed)
      expect(mockClient.post).toHaveBeenCalledWith('/rooms/1/beds/', createBedRequest)
    })

    it('should list beds for a room', async () => {
      const mockBeds = [mockBed]
      const response = { data: mockBeds }
      mockClient.get.mockResolvedValueOnce(response)

      // Get the success interceptor function
      const successInterceptor = mockClient.interceptors.response.use.mock.calls[0][0]

      const result = await api.listBeds(1)
      expect(successInterceptor(response)).toEqual(mockBeds)
      expect(mockClient.get).toHaveBeenCalledWith('/rooms/1/beds/')
    })

    it('should delete a bed', async () => {
      mockClient.delete.mockResolvedValueOnce({ data: null })
      await api.deleteBed(1)
      expect(mockClient.delete).toHaveBeenCalledWith('/beds/1')
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors correctly', async () => {
      const mockError = new Error('Bad Request')
      Object.assign(mockError, {
        response: {
          status: 400,
          data: { message: 'Bad Request' }
        }
      })
      mockClient.post.mockRejectedValueOnce(mockError)

      const createBedRequest: CreateBedRequest = {
        type: 'queen',
        subtype: 'standard',
      }

      await expect(api.createBed(1, createBedRequest)).rejects.toThrow('Bad Request')
    })
  })
})
