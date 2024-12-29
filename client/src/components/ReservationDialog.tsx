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
  onSave: (reservation: CreateReservationRequest) => Promise<void>;
  initialReservation?: Partial<CreateReservationRequest>;
  existingReservation?: {
    id: string;
    guest_name?: string;
    room_name?: string;
  };
  mode?: 'create' | 'edit';
}

export default function ReservationDialog({ 
  open, 
  onClose, 
  onSave,
  initialReservation,
  existingReservation,
  mode = 'create'
}: ReservationDialogProps) {
  const [newReservation, setNewReservation] = useState<Partial<CreateReservationRequest>>({
    guest_id: '',
    room_id: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
    special_requests: ''
  });
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');
  const [pendingRoomId, setPendingRoomId] = useState<string>('');
  const [properties, setProperties] = useState<Property[]>([]);
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [guests, setGuests] = useState<Guest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (open) {
      // Reset state first
      setNewReservation({
        guest_id: '',
        room_id: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
        special_requests: ''
      });
      setSelectedPropertyId('');
      setPendingRoomId('');
      setError(null);
      setSuccessMessage(null);

      // If we have initial data, use it
      if (initialReservation) {
        setNewReservation(prev => ({
          ...prev,
          ...initialReservation,
          guest_id: initialReservation.guest_id?.toString() || '',
          room_id: initialReservation.room_id?.toString() || '',
        }));
        
        if (initialReservation.property_id) {
          setSelectedPropertyId(initialReservation.property_id.toString());
          setPendingRoomId(initialReservation.room_id?.toString() || '');
        }
      }
    }
  }, [open, initialReservation]);

  // Fetch initial data when dialog opens
  useEffect(() => {
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
        console.error('Error fetching initial data:', err);
        setError('Failed to load initial data');
      } finally {
        setLoading(false);
      }
    };

    if (open) {
      fetchInitialData();
    }
  }, [open]);

  // Load rooms when property is selected
  useEffect(() => {
    const fetchPropertyRooms = async () => {
      if (!selectedPropertyId) {
        setRooms([]);
        setBuildings([]);
        return;
      }
      
      try {
        setLoading(true);
        const property = await api.getProperty(Number(selectedPropertyId));
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

        // Now that we have rooms, set the pending room_id if it exists and is valid
        if (pendingRoomId && allRooms.find(r => r.id.toString() === pendingRoomId)) {
          setNewReservation(prev => ({ ...prev, room_id: pendingRoomId }));
          setPendingRoomId('');
        }
      } catch (err) {
        console.error('Error fetching rooms:', err);
        setError('Failed to load rooms');
      } finally {
        setLoading(false);
      }
    };

    fetchPropertyRooms();
  }, [selectedPropertyId]);

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
        num_guests: 1, // Default to 1
        special_requests: newReservation.special_requests || ''
      } as CreateReservationRequest)

    } catch (err: any) {
      console.error('Error creating reservation:', err)
      setError(err.message || 'Failed to create reservation')
    }
  };

  const handleClose = () => {
    setNewReservation({
      guest_id: '',
      room_id: '',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
      special_requests: ''
    });
    setSelectedPropertyId('');
    setPendingRoomId('');
    setError(null);
    setSuccessMessage(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{mode === 'create' ? 'New Reservation' : 'Edit Reservation'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, my: 1 }}>
          <Grid container spacing={1.5}>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Property"
                fullWidth
                size="small"
                value={selectedPropertyId || ''}
                onChange={(e) => {
                  setSelectedPropertyId(e.target.value);
                  setNewReservation(prev => ({ ...prev, room_id: '' }));
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
                value={newReservation.room_id || ''}
                onChange={(e) => setNewReservation(prev => ({ ...prev, room_id: e.target.value }))}
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
                value={newReservation.guest_id || ''}
                onChange={(e) => setNewReservation(prev => ({ ...prev, guest_id: e.target.value }))}
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

            <Grid item xs={12}>
              <TextField
                label="Special Requests"
                fullWidth
                size="small"
                multiline
                rows={2}
                value={newReservation.special_requests}
                onChange={(e) => setNewReservation(prev => ({
                  ...prev,
                  special_requests: e.target.value
                }))}
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
        <Button onClick={handleClose}>
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
          {mode === 'create' ? 'Create' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
