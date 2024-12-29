import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
  MenuItem,
  Alert,
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import { Add as AddIcon } from '@mui/icons-material'
import { api } from '../api'
import type { Reservation, Guest, Room, CreateReservationRequest, Property, Building } from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Reservations() {
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [guests, setGuests] = useState<Guest[]>([])
  const [properties, setProperties] = useState<Property[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [buildings, setBuildings] = useState<Building[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [newReservation, setNewReservation] = useState<Partial<CreateReservationRequest>>({
    guest_id: '',
    room_id: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
    num_guests: 1,
    special_requests: ''
  })
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('')

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      setLoading(true)
      const [guestsData, propertiesData] = await Promise.all([
        api.searchGuests({}),
        api.listProperties(),
      ])
      setGuests(guestsData)
      setProperties(propertiesData)
      setError(null)
    } catch (err) {
      setError('Failed to load initial data')
      console.error('Error fetching initial data:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchPropertyRooms = async (propertyId: string) => {
    try {
      setLoading(true)
      const property = await api.getProperty(Number(propertyId))
      setBuildings(property.buildings)
      
      // Collect all rooms from all buildings
      const allRooms = property.buildings.flatMap(building => 
        building.rooms.map(room => ({
          ...room,
          buildingName: building.name,
          buildingId: building.id
        }))
      )
      setRooms(allRooms)
    } catch (err) {
      setError('Failed to load rooms')
      console.error('Error fetching rooms:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedPropertyId) {
      fetchPropertyRooms(selectedPropertyId)
    }
  }, [selectedPropertyId])

  const handleCreateReservation = async () => {
    if (!newReservation.guest_id || !newReservation.room_id) {
      setError('Please select both guest and room')
      return
    }

    try {
      const reservation = await api.createReservation({
        guest_id: Number(newReservation.guest_id),
        room_id: Number(newReservation.room_id),
        start_date: newReservation.start_date!,  // Send date as YYYY-MM-DD string
        end_date: newReservation.end_date!,      // Send date as YYYY-MM-DD string
        num_guests: newReservation.num_guests!,
        special_requests: newReservation.special_requests
      })
      
      setReservations([...reservations, reservation])
      
      // Show success message
      const guest = guests.find(g => g.id === Number(newReservation.guest_id))
      const room = rooms.find(r => r.id === Number(newReservation.room_id))
      const building = buildings.find(b => b.id === room?.buildingId)
      
      setSuccessMessage(
        `Reservation created successfully!\n\n` +
        `Guest: ${guest?.name}\n` +
        `Building: ${building?.name}\n` +
        `Room: ${room?.name} (${room?.room_number})\n` +
        `Dates: ${new Date(newReservation.start_date!).toLocaleDateString()} - ${new Date(newReservation.end_date!).toLocaleDateString()}\n` +
        `Number of Guests: ${newReservation.num_guests}`
      )
      
      // Don't close dialog, let user review the success message
      setError(null)
    } catch (err: any) {
      if (err.response) {
        // If we have a response from the server, use its error message
        const errorDetail = await err.response.json();
        setError(errorDetail.detail || 'Failed to create reservation');
      } else {
        setError('Failed to create reservation');
      }
      console.error('Error creating reservation:', err)
    }
  }

  const handleCheckAvailability = async () => {
    if (!newReservation.room_id) {
      setError('Please select a room first')
      return
    }

    try {
      const availability = await api.checkRoomAvailability(
        Number(newReservation.room_id),
        newReservation.start_date!,  // Send date as YYYY-MM-DD string
        newReservation.end_date!     // Send date as YYYY-MM-DD string
      )
      
      if (!availability.available) {
        const conflicts = availability.conflicts?.map(conflict => 
          `${conflict.guest_name} (${new Date(conflict.start_date).toLocaleDateString()} - ${new Date(conflict.end_date).toLocaleDateString()})`
        ).join(', ')
        setError(`Room is not available. Existing reservations: ${conflicts}`)
      } else {
        setError(null)
      }
    } catch (err) {
      setError('Failed to check room availability')
      console.error('Error checking availability:', err)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Reservations</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          New Reservation
        </Button>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Grid container spacing={3}>
        {reservations.map((reservation) => (
          <Grid item xs={12} sm={6} md={4} key={reservation.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Reservation #{reservation.id}
                </Typography>
                <Typography color="text.secondary" gutterBottom>
                  Guest: {guests.find(g => g.id === reservation.guestId)?.name}
                </Typography>
                <Typography color="text.secondary" gutterBottom>
                  Room: {rooms.find(r => r.id === reservation.roomId)?.name}
                </Typography>
                <Typography variant="body2">
                  {new Date(reservation.startDate).toLocaleDateString()} - {new Date(reservation.endDate).toLocaleDateString()}
                </Typography>
                <Typography variant="body2">
                  Guests: {reservation.numGuests}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Reservation</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, my: 1 }}>
            <TextField
              select
              label="Property"
              fullWidth
              value={selectedPropertyId}
              onChange={(e) => {
                setSelectedPropertyId(e.target.value)
                setNewReservation({ ...newReservation, room_id: '' }) // Reset room selection
              }}
            >
              <MenuItem value="">
                <em>Select a property</em>
              </MenuItem>
              {properties.map((property) => (
                <MenuItem key={property.id} value={property.id}>
                  {property.name}
                </MenuItem>
              ))}
            </TextField>

            <TextField
              select
              label="Room"
              fullWidth
              value={newReservation.room_id}
              onChange={(e) => setNewReservation({ ...newReservation, room_id: e.target.value })}
              disabled={!selectedPropertyId}
            >
              <MenuItem value="">
                <em>Select a room</em>
              </MenuItem>
              {buildings.map((building) => [
                <MenuItem 
                  key={`building-${building.id}`} 
                  disabled 
                  sx={{ 
                    bgcolor: 'action.hover',
                    fontWeight: 'bold',
                    color: 'text.primary'
                  }}
                >
                  {building.name}
                </MenuItem>,
                ...rooms
                  .filter(room => room.buildingId === building.id)
                  .map(room => (
                    <MenuItem 
                      key={room.id} 
                      value={room.id}
                      sx={{ pl: 4 }}
                    >
                      {room.name} ({room.room_number})
                    </MenuItem>
                  ))
              ])}
            </TextField>

            <TextField
              select
              label="Guest"
              fullWidth
              value={newReservation.guest_id}
              onChange={(e) => setNewReservation({ ...newReservation, guest_id: e.target.value })}
            >
              <MenuItem value="">
                <em>Select a guest</em>
              </MenuItem>
              {guests.map((guest) => (
                <MenuItem key={guest.id} value={guest.id}>
                  {guest.name}
                </MenuItem>
              ))}
            </TextField>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <DatePicker
                label="Check-in Date"
                value={new Date(newReservation.start_date!)}
                onChange={(date) => date && setNewReservation({
                  ...newReservation,
                  start_date: date.toISOString().split('T')[0]
                })}
                sx={{ flex: 1 }}
              />
              <DatePicker
                label="Check-out Date"
                value={new Date(newReservation.end_date!)}
                onChange={(date) => date && setNewReservation({
                  ...newReservation,
                  end_date: date.toISOString().split('T')[0]
                })}
                sx={{ flex: 1 }}
              />
            </Box>

            <TextField
              label="Number of Guests"
              type="number"
              fullWidth
              value={newReservation.num_guests}
              onChange={(e) => setNewReservation({
                ...newReservation,
                num_guests: Number(e.target.value)
              })}
              inputProps={{ min: 1 }}
            />

            <TextField
              label="Special Requests"
              fullWidth
              value={newReservation.special_requests}
              onChange={(e) => setNewReservation({
                ...newReservation,
                special_requests: e.target.value
              })}
            />

            {error && (
              <Typography color="error">
                {error}
              </Typography>
            )}

            {successMessage && (
              <Alert severity="success" sx={{ whiteSpace: 'pre-line' }}>
                {successMessage}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => {
            setOpenDialog(false)
            setSuccessMessage(null)
            setError(null)
            setNewReservation({
              guest_id: '',
              room_id: '',
              start_date: new Date().toISOString().split('T')[0],
              end_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
              num_guests: 1,
              special_requests: ''
            })
            setSelectedPropertyId('')
          }}>
            Close
          </Button>
          <Button onClick={handleCheckAvailability} color="info">
            Check Availability
          </Button>
          <Button 
            onClick={handleCreateReservation} 
            variant="contained"
            disabled={!newReservation.guest_id || !newReservation.room_id}
          >
            Create Reservation
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
