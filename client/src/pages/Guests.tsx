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
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Add as AddIcon, Search as SearchIcon } from '@mui/icons-material'
import { api } from '../api'
import type { Guest, CreateGuestRequest } from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Guests() {
  const [guests, setGuests] = useState<Guest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [newGuest, setNewGuest] = useState<CreateGuestRequest>({
    name: '',
    email: '',
    phone: '',
    contactEmails: [],
  })

  useEffect(() => {
    fetchGuests()
  }, [])

  const fetchGuests = async () => {
    try {
      setLoading(true)
      const data = await api.searchGuests({})
      setGuests(data)
      setError(null)
    } catch (err) {
      setError('Failed to load guests')
      console.error('Error fetching guests:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateGuest = async () => {
    try {
      const guest = await api.createGuest(newGuest)
      setGuests([...guests, guest])
      setOpenDialog(false)
      setNewGuest({
        name: '',
        email: '',
        phone: '',
        contactEmails: [],
      })
      setError(null)
    } catch (err) {
      setError('Failed to create guest')
      console.error('Error creating guest:', err)
    }
  }

  const handleSearch = async () => {
    try {
      setLoading(true)
      const data = await api.searchGuests(searchQuery ? { name: searchQuery } : {})
      setGuests(data)
      setError(null)
    } catch (err) {
      setError('Failed to search guests')
      console.error('Error searching guests:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !guests.length) {
    return <LoadingSpinner />
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Guests</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Add Guest
        </Button>
      </Box>

      <Box sx={{ mb: 4 }}>
        <TextField
          fullWidth
          placeholder="Search guests..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={handleSearch}>
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Grid container spacing={3}>
        {guests.map((guest) => (
          <Grid item xs={12} sm={6} md={4} key={guest.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {guest.name}
                </Typography>
                {guest.email && (
                  <Typography color="text.secondary" gutterBottom>
                    {guest.email}
                  </Typography>
                )}
                {guest.phone && (
                  <Typography color="text.secondary" gutterBottom>
                    {guest.phone}
                  </Typography>
                )}
                {guest.contactEmails?.length > 0 && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Additional Contacts: {guest.contactEmails.join(', ')}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Add New Guest</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Guest Name"
            fullWidth
            required
            value={newGuest.name}
            onChange={(e) => setNewGuest({ ...newGuest, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            value={newGuest.email}
            onChange={(e) => setNewGuest({ ...newGuest, email: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Phone"
            fullWidth
            value={newGuest.phone}
            onChange={(e) => setNewGuest({ ...newGuest, phone: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateGuest}
            variant="contained"
            color="primary"
            disabled={!newGuest.name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
