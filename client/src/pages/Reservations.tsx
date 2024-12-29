import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { api } from '../api'
import type { Reservation, CreateReservationRequest } from '../api'
import LoadingSpinner from '../components/LoadingSpinner'
import ReservationDialog from '../components/ReservationDialog'

export default function Reservations() {
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      setLoading(true)
      const reservationsData = await api.getReservations(
        new Date().toISOString(),
        new Date(Date.now() + 30 * 86400000).toISOString()
      )
      setReservations(reservationsData)
      setError(null)
    } catch (err) {
      setError('Failed to load reservations')
      console.error('Error fetching reservations:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateReservation = async (reservation: CreateReservationRequest) => {
    const created = await api.createReservation(reservation)
    setReservations([...reservations, created])
    setOpenDialog(false)
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
                  Guest: {reservation.guest_name}
                </Typography>
                <Typography color="text.secondary" gutterBottom>
                  Room: {reservation.room_name} ({reservation.room_number})
                </Typography>
                <Typography variant="body2">
                  {new Date(reservation.start_date).toLocaleDateString()} - {new Date(reservation.end_date).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <ReservationDialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        onSave={handleCreateReservation}
      />
    </Box>
  )
}
