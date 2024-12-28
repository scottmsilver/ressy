import { useState, useEffect } from 'react'
import { Link as RouterLink } from 'react-router-dom'
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
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { api } from '../api'
import type { Property, CreatePropertyRequest } from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Properties() {
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [newProperty, setNewProperty] = useState<CreatePropertyRequest>({
    name: '',
    address: '',
  })

  useEffect(() => {
    fetchProperties()
  }, [])

  const fetchProperties = async () => {
    try {
      setLoading(true)
      const data = await api.listProperties()
      setProperties(data)
      setError(null)
    } catch (err) {
      setError('Failed to load properties')
      console.error('Error fetching properties:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProperty = async () => {
    try {
      const property = await api.createProperty(newProperty)
      setProperties([...properties, property])
      setOpenDialog(false)
      setNewProperty({ name: '', address: '' })
      setError(null)
    } catch (err) {
      setError('Failed to create property')
      console.error('Error creating property:', err)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Properties</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Add Property
        </Button>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Grid container spacing={3}>
        {properties.map((property) => (
          <Grid item xs={12} sm={6} md={4} key={property.id}>
            <Card
              component={RouterLink}
              to={`/properties/${property.id}`}
              sx={{
                height: '100%',
                textDecoration: 'none',
                color: 'inherit',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                },
              }}
            >
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {property.name}
                </Typography>
                <Typography color="text.secondary">{property.address}</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Buildings: {property.buildings?.length || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Add New Property</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Property Name"
            fullWidth
            value={newProperty.name}
            onChange={(e) => setNewProperty({ ...newProperty, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Address"
            fullWidth
            value={newProperty.address}
            onChange={(e) => setNewProperty({ ...newProperty, address: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateProperty}
            variant="contained"
            color="primary"
            disabled={!newProperty.name || !newProperty.address}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
