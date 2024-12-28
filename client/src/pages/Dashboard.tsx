import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
} from '@mui/material'
import {
  Hotel as HotelIcon,
  Person as PersonIcon,
  EventAvailable as EventIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material'
import { api } from '../api'
import type { Property, Guest, Reservation } from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Dashboard() {
  const navigate = useNavigate()
  const [properties, setProperties] = useState<Property[]>([])
  const [guests, setGuests] = useState<Guest[]>([])
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const [propertiesData, guestsData, reservationsData] = await Promise.all([
        api.listProperties(),
        api.searchGuests({}),
        // TODO: Add proper date range for reservations
        api.getReservations(new Date().toISOString(), new Date(Date.now() + 7 * 86400000).toISOString())
      ])
      setProperties(propertiesData)
      setGuests(guestsData)
      setReservations(reservationsData)
      setError(null)
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error('Error fetching dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  const stats = {
    totalProperties: properties.length,
    totalRooms: properties.reduce(
      (acc, p) => acc + p.buildings.reduce((acc, b) => acc + b.rooms.length, 0),
      0
    ),
    totalGuests: guests.length,
    upcomingReservations: reservations.length,
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <HotelIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Properties</Typography>
              </Box>
              <Typography variant="h4">{stats.totalProperties}</Typography>
              <Typography variant="body2" color="text.secondary">
                Total Rooms: {stats.totalRooms}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PersonIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Guests</Typography>
              </Box>
              <Typography variant="h4">{stats.totalGuests}</Typography>
              <Button
                size="small"
                color="primary"
                onClick={() => navigate('/guests')}
              >
                View All
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <EventIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Upcoming</Typography>
              </Box>
              <Typography variant="h4">{stats.upcomingReservations}</Typography>
              <Button
                size="small"
                color="primary"
                onClick={() => navigate('/reservations')}
              >
                View All
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUpIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Reports</Typography>
              </Box>
              <Button
                size="small"
                color="primary"
                onClick={() => navigate('/reports')}
              >
                View Reports
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Properties */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Properties
              </Typography>
              <Grid container spacing={2}>
                {properties.slice(0, 3).map((property) => (
                  <Grid item xs={12} key={property.id}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <Box>
                        <Typography variant="subtitle1">{property.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {property.address}
                        </Typography>
                      </Box>
                      <Button
                        size="small"
                        onClick={() => navigate(`/properties/${property.id}`)}
                      >
                        View
                      </Button>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Reservations */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Reservations
              </Typography>
              <Grid container spacing={2}>
                {reservations.slice(0, 3).map((reservation) => (
                  <Grid item xs={12} key={reservation.id}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <Box>
                        <Typography variant="subtitle1">
                          {guests.find(g => g.id === reservation.guestId)?.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(reservation.startDate).toLocaleDateString()} -{' '}
                          {new Date(reservation.endDate).toLocaleDateString()}
                        </Typography>
                      </Box>
                      <Typography
                        variant="body2"
                        sx={{
                          px: 1,
                          py: 0.5,
                          borderRadius: 1,
                          bgcolor: 'success.light',
                          color: 'success.contrastText',
                        }}
                      >
                        {reservation.status}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
