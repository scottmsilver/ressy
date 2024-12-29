import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Button,
  TextField,
  MenuItem,
  Typography,
  Alert,
  Grid
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import { api } from '../api';
import type { Guest, Room, CreateReservationRequest, Property, Building } from '../api';

interface ReservationDialogProps {
  open: boolean;
  onClose: () => void;
  initialReservation?: Partial<CreateReservationRequest>;
  onSave: (reservation: CreateReservationRequest) => Promise<void>;
}

export default function ReservationDialog({ open, onClose, initialReservation, onSave }: ReservationDialogProps) {
  const [guests, setGuests] = useState<Guest[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [newReservation, setNewReservation] = useState<Partial<CreateReservationRequest>>(
    initialReservation || {
      guest_id: '',
      room_id: '',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
      num_guests: 1,
      special_requests: ''
    }
  );

  useEffect(() => {
    if (initialReservation) {
      setNewReservation(prev => ({
        ...prev,
        ...initialReservation
      }));

      // If we have a property ID, set it
      if (initialReservation.property_id) {
        setSelectedPropertyId(initialReservation.property_id.toString());
      }
    }
  }, [initialReservation]);

  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');

  useEffect(() => {
    if (selectedPropertyId) {
      fetchPropertyRooms(selectedPropertyId);
    }
  }, [selectedPropertyId]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (initialReservation?.room_id) {
      // Find the property for this room
      api.getProperty(parseInt(initialReservation.room_id))
        .then(property => {
          const room = property.buildings
            .flatMap(b => b.rooms)
            .find(r => r.id.toString() === initialReservation.room_id);
          
          if (room) {
            setSelectedPropertyId(property.id.toString());
          }
        })
        .catch(console.error);
    }
  }, [initialReservation?.room_id]);

  useEffect(() => {
    if (rooms.length > 0 && newReservation.room_id) {
      const room = rooms.find(r => r.id.toString() === newReservation.room_id);
      if (room) {
        setNewReservation(prev => ({
          ...prev,
          room_id: room.id.toString()
        }));
      }
    }
  }, [rooms, newReservation.room_id]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [guestsData, propertiesData] = await Promise.all([
        api.searchGuests({}),
        api.listProperties(),
      ]);
      setGuests(guestsData);
      setProperties(propertiesData);
      setError(null);
    } catch (err) {
      setError('Failed to load initial data');
      console.error('Error fetching initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPropertyRooms = async (propertyId: string) => {
    try {
      setLoading(true);
      const property = await api.getProperty(Number(propertyId));
      setBuildings(property.buildings);
      
      // Collect all rooms from all buildings
      const allRooms = property.buildings.flatMap(building => 
        building.rooms.map(room => ({
          ...room,
          buildingName: building.name,
          buildingId: building.id
        }))
      );
      setRooms(allRooms);
    } catch (err) {
      setError('Failed to load rooms');
      console.error('Error fetching rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckAvailability = async () => {
    if (!newReservation.room_id) {
      setError('Please select a room first')
      return
    }

    try {
      setError(null)
      setSuccessMessage(null)
      
      const availability = await api.checkRoomAvailability(
        Number(newReservation.room_id),
        newReservation.start_date!,
        newReservation.end_date!
      )
      
      if (!availability.available) {
        const conflicts = availability.conflicts?.map(conflict => 
          `${conflict.guest_name} (${new Date(conflict.start_date).toLocaleDateString()} - ${new Date(conflict.end_date).toLocaleDateString()})`
        ).join(', ')
        setError(`Room is not available. Existing reservations: ${conflicts}`)
      } else {
        setError(null)
        setSuccessMessage('Room is available for these dates!')
      }
    } catch (err: any) {
      console.error('Error checking availability:', err)
      setError(err.message || 'Failed to check room availability')
    }
  };

  const handleSave = async () => {
    if (!newReservation.room_id || !newReservation.guest_id) {
      setError('Please select both room and guest')
      return
    }

    try {
      setError(null)
      setSuccessMessage(null)

      // Check availability first
      const availability = await api.checkRoomAvailability(
        Number(newReservation.room_id),
        newReservation.start_date!,
        newReservation.end_date!
      )
      
      if (!availability.available) {
        const conflicts = availability.conflicts?.map(conflict => 
          `${conflict.guest_name} (${new Date(conflict.start_date).toLocaleDateString()} - ${new Date(conflict.end_date).toLocaleDateString()})`
        ).join(', ')
        setError(`Room is not available. Existing reservations: ${conflicts}`)
        return
      }

      // If available, create the reservation
      await onSave({
        guest_id: Number(newReservation.guest_id),
        room_id: Number(newReservation.room_id),
        start_date: newReservation.start_date!,
        end_date: newReservation.end_date!,
        num_guests: newReservation.num_guests || 1,
        special_requests: newReservation.special_requests || ''
      } as CreateReservationRequest)

    } catch (err: any) {
      console.error('Error creating reservation:', err)
      setError(err.message || 'Failed to create reservation')
    }
  };

  const handleClose = () => {
    setSuccessMessage(null);
    setError(null);
    setNewReservation({
      guest_id: '',
      room_id: '',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
      num_guests: 1,
      special_requests: ''
    });
    setSelectedPropertyId('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>New Reservation</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, my: 1 }}>
          <Grid container spacing={1.5}>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Property"
                fullWidth
                size="small"
                value={selectedPropertyId}
                onChange={(e) => {
                  setSelectedPropertyId(e.target.value)
                  setNewReservation({ ...newReservation, room_id: '' })
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
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Room"
                fullWidth
                size="small"
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
                    sx={{ bgcolor: 'action.hover', fontWeight: 'bold' }}
                  >
                    {building.name}
                  </MenuItem>,
                  ...rooms
                    .filter(room => room.buildingId === building.id)
                    .map(room => (
                      <MenuItem key={room.id} value={room.id} sx={{ pl: 4 }}>
                        {room.name} ({room.room_number})
                      </MenuItem>
                    ))
                ])}
              </TextField>
            </Grid>

            <Grid item xs={12} sm={6}>
              <DatePicker
                label="Check-in"
                value={new Date(newReservation.start_date!)}
                onChange={(date) => date && setNewReservation({
                  ...newReservation,
                  start_date: date.toISOString().split('T')[0]
                })}
                slotProps={{ textField: { size: 'small', fullWidth: true } }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <DatePicker
                label="Check-out"
                value={new Date(newReservation.end_date!)}
                onChange={(date) => date && setNewReservation({
                  ...newReservation,
                  end_date: date.toISOString().split('T')[0]
                })}
                slotProps={{ textField: { size: 'small', fullWidth: true } }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Guest"
                fullWidth
                size="small"
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
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                label="Number of Guests"
                type="number"
                fullWidth
                size="small"
                value={newReservation.num_guests}
                onChange={(e) => setNewReservation({
                  ...newReservation,
                  num_guests: Number(e.target.value)
                })}
                inputProps={{ min: 1 }}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                label="Special Requests"
                fullWidth
                size="small"
                multiline
                rows={2}
                value={newReservation.special_requests}
                onChange={(e) => setNewReservation({
                  ...newReservation,
                  special_requests: e.target.value
                })}
              />
            </Grid>
          </Grid>

          {error && (
            <Typography color="error" variant="body2">
              {error}
            </Typography>
          )}

          {successMessage && (
            <Alert severity="success" sx={{ mt: 1 }}>
              {successMessage}
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={() => {
          onClose();
          setSuccessMessage(null);
          setError(null);
        }}>
          Cancel
        </Button>
        <Button onClick={handleCheckAvailability} color="info">
          Check Availability
        </Button>
        <Button 
          onClick={handleSave}
          variant="contained"
          disabled={!newReservation.room_id || !newReservation.guest_id}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  );
}
