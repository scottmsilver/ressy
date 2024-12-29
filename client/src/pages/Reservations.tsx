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
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import { Add as AddIcon } from '@mui/icons-material'
import { api } from '../api'
import type { Reservation, Guest, Room, CreateReservationRequest } from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Reservations() {
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [guests, setGuests] = useState<Guest[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [newReservation, setNewReservation] = useState<Partial<CreateReservationRequest>>({
    guestId: '',
    roomId: '',
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date(Date.now() + 86400000).toISOString().split('T')[0],
    numGuests: 1,
  })

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      setLoading(true)
      const [guestsData, roomsData] = await Promise.all([
        api.searchGuests({}),
        api.listRooms(1), // TODO: Replace with proper building ID
      ])
      setGuests(guestsData)
      setRooms(roomsData)
      setError(null)
    } catch (err) {
      setError('Failed to load initial data')
      console.error('Error fetching initial data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateReservation = async () => {
    if (!newReservation.guestId || !newReservation.roomId) {
      setError('Please select both guest and room')
      return
    }

    try {
      const reservation = await api.createReservation({
        guestId: Number(newReservation.guestId),
        roomId: Number(newReservation.roomId),
        startDate: newReservation.startDate!,
        endDate: newReservation.endDate!,
        numGuests: newReservation.numGuests!,
      })
      setReservations([...reservations, reservation])
      setOpenDialog(false)
      setNewReservation({
        guestId: '',
        roomId: '',
        startDate: new Date().toISOString().split('T')[0],
        endDate: new Date(Date.now() + 86400000).toISOString().split('T')[0],
        numGuests: 1,
      })
      setError(null)
    } catch (err) {
      setError('Failed to create reservation')
      console.error('Error creating reservation:', err)
    }
  }

  const handleCheckAvailability = async () => {
    if (!newReservation.roomId) {
      setError('Please select a room first')
      return
    }

    try {
      const availability = await api.checkRoomAvailability(
        Number(newReservation.roomId),
        newReservation.startDate!,
        newReservation.endDate!
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
              label="Guest"
              fullWidth
              value={newReservation.guestId}
              onChange={(e) => setNewReservation({ ...newReservation, guestId: e.target.value })}
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
            <TextField
              select
              label="Room"
              fullWidth
              value={newReservation.roomId}
              onChange={(e) => setNewReservation({ ...newReservation, roomId: e.target.value })}
            >
              <MenuItem value="">
                <em>Select a room</em>
              </MenuItem>
              {rooms.map((room) => (
                <MenuItem key={room.id} value={room.id}>
                  {room.name} ({room.roomNumber})
                </MenuItem>
              ))}
            </TextField>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <DatePicker
                label="Check-in Date"
                value={new Date(newReservation.startDate!)}
                onChange={(date) => date && setNewReservation({
                  ...newReservation,
                  startDate: date.toISOString().split('T')[0]
                })}
                sx={{ flex: 1 }}
              />
              <DatePicker
                label="Check-out Date"
                value={new Date(newReservation.endDate!)}
                onChange={(date) => date && setNewReservation({
                  ...newReservation,
                  endDate: date.toISOString().split('T')[0]
                })}
                sx={{ flex: 1 }}
              />
            </Box>
            <TextField
              label="Number of Guests"
              type="number"
              fullWidth
              value={newReservation.numGuests}
              onChange={(e) => setNewReservation({
                ...newReservation,
                numGuests: Number(e.target.value)
              })}
              inputProps={{ min: 1 }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCheckAvailability} color="info">
            Check Availability
          </Button>
          <Button onClick={handleCreateReservation} variant="contained">
            Create Reservation
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
