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
  const [newReservation, setNewReservation] = useState<CreateReservationRequest>({
    guestId: 0,
    roomId: 0,
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
    try {
      const reservation = await api.createReservation(newReservation)
      setReservations([...reservations, reservation])
      setOpenDialog(false)
      setNewReservation({
        guestId: 0,
        roomId: 0,
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
    try {
      const availability = await api.checkRoomAvailability(
        newReservation.roomId,
        newReservation.startDate,
        newReservation.endDate
      )
      if (!availability.available) {
        setError('Room is not available for the selected dates')
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

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>New Reservation</DialogTitle>
        <DialogContent>
          <TextField
            select
            margin="dense"
            label="Guest"
            fullWidth
            value={newReservation.guestId}
            onChange={(e) => setNewReservation({ ...newReservation, guestId: Number(e.target.value) })}
          >
            {guests.map((guest) => (
              <MenuItem key={guest.id} value={guest.id}>
                {guest.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            margin="dense"
            label="Room"
            fullWidth
            value={newReservation.roomId}
            onChange={(e) => setNewReservation({ ...newReservation, roomId: Number(e.target.value) })}
          >
            {rooms.map((room) => (
              <MenuItem key={room.id} value={room.id}>
                {room.name} ({room.roomNumber})
              </MenuItem>
            ))}
          </TextField>
          <DatePicker
            label="Check-in Date"
            value={new Date(newReservation.startDate)}
            onChange={(date) => date && setNewReservation({
              ...newReservation,
              startDate: date.toISOString().split('T')[0]
            })}
          />
          <DatePicker
            label="Check-out Date"
            value={new Date(newReservation.endDate)}
            onChange={(date) => date && setNewReservation({
              ...newReservation,
              endDate: date.toISOString().split('T')[0]
            })}
          />
          <TextField
            margin="dense"
            label="Number of Guests"
            type="number"
            fullWidth
            value={newReservation.numGuests}
            onChange={(e) => setNewReservation({
              ...newReservation,
              numGuests: Number(e.target.value)
            })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCheckAvailability} color="primary">
            Check Availability
          </Button>
          <Button
            onClick={handleCreateReservation}
            variant="contained"
            color="primary"
            disabled={!newReservation.guestId || !newReservation.roomId}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
