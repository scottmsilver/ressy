import { describe, it, expect, beforeEach } from 'vitest'
import { RessyApi } from '../RessyApi'
import { CreateRoomRequest, Room, BedType, BedSubType, CreateBedRequest, Bed } from '../types'

describe('RessyApi Live Tests', () => {
  let api: RessyApi
  let buildingId: number

  beforeEach(() => {
    // Create a new instance of RessyApi pointing to local development server
    api = new RessyApi('http://127.0.0.1:8000')
  })

  describe('Health Check', () => {
    it('should confirm API is healthy', async () => {
      const result = await api.checkHealth()
      expect(result).toBe(true)
    })
  })

  describe('Room Management', () => {
    let createdRoomId: number

    beforeEach(async () => {
      // Create a test property
      const property = await api.createProperty({
        name: 'Test Property',
        address: '123 Test St',
        city: 'Test City',
        state: 'TS',
        zipCode: '12345'
      })

      // Create a test building
      const building = await api.createBuilding(property.id, {
        name: 'Test Building',
        floors: 1
      })
      buildingId = building.id

      // Create a test room
      const room = await api.createRoom(buildingId, {
        name: 'Test Room',
        room_number: '101'
      })
      expect(room).toBeDefined()
      expect(room.id).toBeDefined()
      createdRoomId = room.id
    })

    it('should create and manage rooms', async () => {
      // Create a room
      const createRoomRequest: CreateRoomRequest = {
        name: 'Test Room 2',
        room_number: '102'
      }

      const createdRoom = await api.createRoom(buildingId, createRoomRequest)
      expect(createdRoom).toBeDefined()
      expect(createdRoom.name).toBe(createRoomRequest.name)
      expect(createdRoom.room_number).toBe(createRoomRequest.room_number)

      // Update room amenities
      const updatedAmenities = ['wifi', 'tv', 'minibar']
      const updatedRoom = await api.updateRoomAmenities(createdRoom.id, updatedAmenities)
      expect(updatedRoom.amenities).toEqual(updatedAmenities)

      // List rooms
      const rooms = await api.listRooms(buildingId)
      expect(rooms.length).toBeGreaterThan(0)
      expect(rooms.some(room => room.id === createdRoom.id)).toBe(true)
    })

    it('should check room availability', async () => {
      const startDate = '2024-12-28'
      const endDate = '2024-12-29'
      const availability = await api.checkRoomAvailability(createdRoomId, startDate, endDate)
      expect(availability).toBeDefined()
      expect(typeof availability.available).toBe('boolean')
      expect(availability.available).toBe(true)  // Room should be available since we haven't made any reservations
    })

    it('should create a bed in a room', async () => {
      // Create a test room first
      const room = await api.createRoom(buildingId, {
        name: 'Test Room with Bed',
        room_number: '201'
      })
      expect(room).toBeDefined()
      expect(room.id).toBeDefined()

      // Create a bed in the room
      const bed = await api.createBed(room.id, {
        type: BedType.QUEEN,
        subtype: BedSubType.STANDARD
      })
      expect(bed).toBeDefined()
      expect(bed.id).toBeDefined()
      expect(bed.bed_type).toBe(BedType.QUEEN)
      expect(bed.bed_subtype).toBe(BedSubType.STANDARD)
      expect(bed.capacity).toBe(2)  // QUEEN beds have capacity of 2
    })

    it('should manage beds in a room', async () => {
      // Create a test room first
      const room = await api.createRoom(buildingId, {
        name: 'Test Room with Multiple Beds',
        room_number: '301'
      })
      expect(room).toBeDefined()
      expect(room.id).toBeDefined()

      // Initially should have no beds
      const initialBeds = await api.listBeds(room.id)
      expect(initialBeds).toHaveLength(0)

      // Create beds of different types
      const beds = await Promise.all([
        api.createBed(room.id, {
          type: BedType.SINGLE,
          subtype: BedSubType.STANDARD
        }),
        api.createBed(room.id, {
          type: BedType.DOUBLE,
          subtype: BedSubType.STANDARD
        }),
        api.createBed(room.id, {
          type: BedType.KING,
          subtype: BedSubType.STANDARD
        })
      ])

      // Verify beds were created
      expect(beds).toHaveLength(3)
      expect(beds[0].bed_type).toBe(BedType.SINGLE)
      expect(beds[0].capacity).toBe(1)  // SINGLE bed has capacity 1
      expect(beds[1].bed_type).toBe(BedType.DOUBLE)
      expect(beds[1].capacity).toBe(2)  // DOUBLE bed has capacity 2
      expect(beds[2].bed_type).toBe(BedType.KING)
      expect(beds[2].capacity).toBe(2)  // KING bed has capacity 2

      // List all beds
      const allBeds = await api.listBeds(room.id)
      expect(allBeds).toHaveLength(3)

      // Delete a bed
      await api.deleteBed(beds[0].id)

      // Verify bed was deleted
      const remainingBeds = await api.listBeds(room.id)
      expect(remainingBeds).toHaveLength(2)
      expect(remainingBeds.find(b => b.id === beds[0].id)).toBeUndefined()
    })
  })
})
