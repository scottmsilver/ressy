import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  Alert,
  Fab,
  Stack,
  Menu,
  DialogContentText,
  Chip
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import { RessyApi } from '../api/core/RessyApi'
import { Property, Room, Building, CreateBedRequest, Bed, BedType, BedSubType } from '../api/core/types'

const api = new RessyApi('http://localhost:8000');

type DialogType = 'bed' | 'building' | 'room' | 'editBuilding' | 'editRoom' | 'deleteBuilding' | 'deleteRoom' | 'deleteBed' | 'editProperty' | null;

interface MenuState {
  element: HTMLElement | null;
  type: 'building' | 'room' | null;
  data: Building | Room | null;
}

export default function PropertyDetails() {
  const { id } = useParams<{ id: string }>()
  const [property, setProperty] = useState<Property | null>(null)
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null)
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null)
  const [selectedBed, setSelectedBed] = useState<Bed | null>(null)
  const [openDialog, setOpenDialog] = useState<DialogType>(null)
  const [bedType, setBedType] = useState<BedType>(BedType.SINGLE)
  const [bedSubtype, setBedSubtype] = useState<BedSubType>(BedSubType.STANDARD)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newBuildingName, setNewBuildingName] = useState('')
  const [newRoomData, setNewRoomData] = useState({
    name: '',
    room_number: '',
    amenities: [] as string[],
  })
  const [menuState, setMenuState] = useState<MenuState>({
    element: null,
    type: null,
    data: null,
  })

  useEffect(() => {
    const fetchPropertyDetails = async () => {
      if (!id) return;

      try {
        setLoading(true);
        setError(null);
        const propertyData = await api.getProperty(parseInt(id));
        
        // Fetch rooms and beds for each building
        const buildingsWithRooms = await Promise.all(
          propertyData.buildings.map(async (building) => {
            const rooms = await api.listRooms(building.id);
            // Fetch beds for each room
            const roomsWithBeds = await Promise.all(
              rooms.map(async (room) => {
                const beds = await api.listBeds(room.id);
                return {
                  ...room,
                  beds: beds || [],
                };
              })
            );
            return {
              ...building,
              rooms: roomsWithBeds,
            };
          })
        );

        setProperty({
          ...propertyData,
          buildings: buildingsWithRooms,
        });
      } catch (error) {
        console.error('Error fetching property:', error);
        setError(error instanceof Error ? error.message : 'Failed to load property');
      } finally {
        setLoading(false);
      }
    };
    fetchPropertyDetails()
  }, [id])

  const handleAddBed = async () => {
    if (!selectedRoom) return

    try {
      setError(null)
      console.log('Adding bed to room:', selectedRoom.id, { type: bedType, subtype: bedSubtype })

      const newBed = await api.createBed(selectedRoom.id, {
        type: bedType,
        subtype: bedSubtype,
      })

      console.log('New bed created:', newBed)

      // Update the local state with the new bed
      if (property) {
        const updatedProperty = {
          ...property,
          buildings: property.buildings.map((building: Building) => ({
            ...building,
            rooms: building.rooms.map((room: Room) =>
              room.id === selectedRoom.id
                ? { ...room, beds: [...(room.beds || []), newBed] }
                : room
            ),
          })),
        }
        console.log('Updating property with new bed:', updatedProperty)
        setProperty(updatedProperty)
      }

      handleCloseDialog()
    } catch (error) {
      console.error('Failed to add bed:', error)
      setError(error instanceof Error ? error.message : 'Failed to add bed')
    }
  }

  const handleAddBuilding = async () => {
    if (!property) return;

    try {
      setError(null);
      const building = await api.createBuilding(property.id, {
        name: newBuildingName.trim(),
      });

      // Update property state with new building
      setProperty({
        ...property,
        buildings: [...property.buildings, { ...building, rooms: [] }],
      });

      handleCloseDialog();
      setNewBuildingName('');
    } catch (error) {
      console.error('Failed to create building:', error);
      setError(error instanceof Error ? error.message : 'Failed to create building');
    }
  }

  const handleAddRoom = async () => {
    if (!property || !selectedBuilding) return

    try {
      setError(null);
      const room = await api.createRoom(selectedBuilding.id, {
        name: newRoomData.name.trim(),
        room_number: newRoomData.room_number.trim(),
        amenities: newRoomData.amenities,
      });

      // Update the property state with new room
      setProperty({
        ...property,
        buildings: property.buildings.map((building) =>
          building.id === selectedBuilding.id
            ? { ...building, rooms: [...building.rooms, { ...room, beds: [] }] }
            : building
        ),
      });

      handleCloseDialog();
      // Reset room data
      setNewRoomData({
        name: '',
        room_number: '',
        amenities: [],
      });
    } catch (error) {
      console.error('Failed to create room:', error);
      setError(error instanceof Error ? error.message : 'Failed to create room');
    }
  }

  const handleDeleteBed = async (roomId: number, bed: Bed) => {
    setSelectedRoom({ id: roomId } as Room)
    setSelectedBed(bed)
    setOpenDialog('deleteBed')
  }

  const handleConfirmDeleteBed = async () => {
    if (!property || !selectedRoom || !selectedBed) return

    try {
      setError(null)
      await api.deleteBed(selectedBed.id)

      // Update the local state
      setProperty({
        ...property,
        buildings: property.buildings.map((building: Building) => ({
          ...building,
          rooms: building.rooms.map((room: Room) =>
            room.id === selectedRoom.id
              ? { ...room, beds: room.beds.filter((b) => b.id !== selectedBed.id) }
              : room
          ),
        })),
      })

      handleCloseDialog()
    } catch (error) {
      console.error('Failed to delete bed:', error)
      setError(error instanceof Error ? error.message : 'Failed to delete bed')
    }
  }

  const handleConfirmDeleteBuilding = async () => {
    if (!property || !selectedBuilding) return

    try {
      setError(null)
      await api.deleteBuilding(selectedBuilding.id)

      setProperty({
        ...property,
        buildings: property.buildings.filter(b => b.id !== selectedBuilding.id),
      })

      handleCloseDialog()
    } catch (error) {
      console.error('Failed to delete building:', error)
      setError(error instanceof Error ? error.message : 'Failed to delete building')
    }
  }

  const handleConfirmDeleteRoom = async () => {
    if (!property || !selectedRoom) return

    try {
      setError(null)
      await api.deleteRoom(selectedRoom.id)

      setProperty({
        ...property,
        buildings: property.buildings.map(building => ({
          ...building,
          rooms: building.rooms.filter(r => r.id !== selectedRoom.id),
        })),
      })
      handleCloseDialog()
    } catch (error) {
      console.error('Failed to delete room:', error)
      setError(error instanceof Error ? error.message : 'Failed to delete room')
    }
  }

  const handleEditProperty = async () => {
    if (!property) return;

    try {
      setError(null);
      const updatedProperty = await api.updateProperty(property.id, {
        name: property.name,
        address: property.address,
      });

      setProperty({
        ...updatedProperty,
        buildings: property.buildings, // Preserve buildings since API response doesn't include them
      });

      handleCloseDialog();
    } catch (error) {
      console.error('Failed to update property:', error);
      setError(error instanceof Error ? error.message : 'Failed to update property');
    }
  };

  const handleEditBuilding = async () => {
    if (!property || !selectedBuilding || !newBuildingName.trim()) return;

    try {
      setError(null);
      const updatedBuilding = await api.updateBuilding(selectedBuilding.id, {
        name: newBuildingName.trim(),
      });

      setProperty({
        ...property,
        buildings: property.buildings.map(b =>
          b.id === selectedBuilding.id ? { ...updatedBuilding, rooms: b.rooms } : b
        ),
      });

      handleCloseDialog();
    } catch (error) {
      console.error('Failed to update building:', error);
      setError(error instanceof Error ? error.message : 'Failed to update building');
    }
  };

  const handleRoomEdit = async (roomId: number, data: { name?: string; room_number?: string; amenities?: string[] }) => {
    try {
      const updatedRoom = await api.updateRoom(roomId, data);
      return updatedRoom;
    } catch (error) {
      console.error('Failed to update room:', error);
      throw error;
    }
  };

  const handleEditRoom = async () => {
    console.log('handleEditRoom called', { selectedRoom, selectedBuilding, newRoomData });
    if (!property || !selectedRoom || !selectedBuilding) {
      console.log('Missing required data', { property, selectedRoom, selectedBuilding });
      return;
    }

    try {
      setError(null);
      console.log('Updating room with data:', {
        roomId: selectedRoom.id,
        data: {
          name: newRoomData.name.trim(),
          room_number: newRoomData.room_number.trim(),
          amenities: newRoomData.amenities,
        }
      });
      
      await handleRoomEdit(selectedRoom.id, {
        name: newRoomData.name.trim(),
        room_number: newRoomData.room_number.trim(),
        amenities: newRoomData.amenities,
      });

      // Refresh the rooms list to ensure UI is in sync
      const updatedRooms = await api.listRooms(selectedBuilding.id);
      
      // Fetch beds for each room
      const roomsWithBeds = await Promise.all(
        updatedRooms.map(async (room) => {
          const beds = await api.listBeds(room.id);
          return {
            ...room,
            beds: beds || [],
          };
        })
      );

      setProperty({
        ...property,
        buildings: property.buildings.map((building) =>
          building.id === selectedBuilding.id
            ? { ...building, rooms: roomsWithBeds }
            : building
        ),
      });

      handleCloseDialog();
    } catch (error) {
      console.error('Failed to edit room:', error);
      setError(error instanceof Error ? error.message : 'Failed to edit room');
    }
  };

  const handleMenuOpen = (
    event: React.MouseEvent<HTMLButtonElement>,
    type: 'building' | 'room',
    data: Building | Room
  ) => {
    setMenuState({
      element: event.currentTarget,
      type,
      data,
    })
  }

  const handleMenuClose = () => {
    setMenuState({
      element: null,
      type: null,
      data: null,
    })
  }

  const handleMenuAction = (action: 'edit' | 'delete') => {
    const { type, data } = menuState
    handleMenuClose()

    if (!data) return

    if (action === 'edit') {
      if (type === 'building') {
        setSelectedBuilding(data as Building)
        setNewBuildingName((data as Building).name)
        setOpenDialog('editBuilding')
      } else if (type === 'room') {
        const room = data as Room
        // Find the building that contains this room
        const building = property?.buildings.find(b => b.id === room.building_id)
        if (building) {
          setSelectedBuilding(building)
        }
        setSelectedRoom(room)
        setNewRoomData({
          name: room.name,
          room_number: room.room_number,
          amenities: room.amenities || [],
        })
        setOpenDialog('editRoom')
      }
    } else if (action === 'delete') {
      if (type === 'building') {
        setSelectedBuilding(data as Building)
        setOpenDialog('deleteBuilding')
      } else if (type === 'room') {
        const room = data as Room
        const building = property?.buildings.find(b => b.id === room.building_id)
        if (building) {
          setSelectedBuilding(building)
        }
        setSelectedRoom(room)
        setOpenDialog('deleteRoom')
      }
    }
  }

  const handleOpenDialog = (
    type: DialogType,
    room?: Room,
    building?: Building
  ) => {
    console.log('handleOpenDialog called with:', { type, room, building });
    setOpenDialog(type);
    
    if (room) {
      console.log('Setting selected room:', room);
      setSelectedRoom(room);
      // Find and set the building for this room
      const roomBuilding = property?.buildings.find(b => b.id === room.building_id);
      if (roomBuilding) {
        console.log('Setting selected building from room:', roomBuilding);
        setSelectedBuilding(roomBuilding);
      }
      setNewRoomData({
        name: room.name,
        room_number: room.room_number,
        amenities: room.amenities || [],
      });
    } else {
      console.log('Resetting room data for new room');
      setSelectedRoom(null);
      setNewRoomData({
        name: '',
        room_number: '',
        amenities: [],
      });
    }

    if (building) {
      console.log('Setting selected building:', building);
      setSelectedBuilding(building);
    }
  }

  const handleCloseDialog = () => {
    setOpenDialog(null)
    setSelectedRoom(null)
    setSelectedBuilding(null)
    setSelectedBed(null)
    setNewBuildingName('')
    setNewRoomData({
      name: '',
      room_number: '',
      amenities: [],
    })
  }

  const calculateRoomCapacity = (room: Room): number => {
    if (!room.beds) return 0;
    return room.beds.reduce((total, bed) => {
      // Single beds have capacity 1, double beds have capacity 2
      return total + (bed.bed_type === BedType.DOUBLE ? 2 : 1);
    }, 0);
  }

  const formatRoomLabel = (room: Room): string => {
    return `${room.name} (Room ${room.room_number})`;
  }

  const formatBedInfo = (bed: Bed): string => {
    return `${bed.bed_type} - ${bed.bed_subtype}`;
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (!property) {
    return (
      <Box p={3}>
        <Alert severity="info">Property not found</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      ) : property ? (
        <>
          <Box 
            sx={{ 
              mb: 4,
              '&:hover .property-actions': {
                opacity: 1,
              },
            }}
          >
            <Stack direction="row" alignItems="center" spacing={2}>
              <Stack direction="row" spacing={1} alignItems="baseline">
                <Typography variant="h4" component="h1">
                  {property.name}
                </Typography>
                <Typography variant="h5" color="text.secondary">
                  ({property.buildings.reduce((total, building) => 
                    total + building.rooms.reduce((roomTotal, room) => 
                      roomTotal + calculateRoomCapacity(room), 0), 0)})
                </Typography>
              </Stack>
              <Stack 
                direction="row" 
                spacing={1}
                className="property-actions"
                sx={{ 
                  opacity: 0,
                  transition: 'opacity 0.2s ease-in-out',
                }}
              >
                <IconButton 
                  size="small"
                  onClick={() => setOpenDialog('editProperty')}
                  sx={{ 
                    bgcolor: 'background.paper',
                    '&:hover': { bgcolor: 'action.hover' },
                  }}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => setOpenDialog('building')}
                  sx={{ 
                    bgcolor: 'background.paper',
                    '&:hover': { bgcolor: 'action.hover' },
                  }}
                >
                  <AddIcon fontSize="small" />
                </IconButton>
              </Stack>
            </Stack>
            <Typography variant="subtitle1" color="text.secondary" sx={{ mt: 1 }}>
              {property.address}
            </Typography>
          </Box>

          {/* Buildings Section */}
          <Stack spacing={3}>
            {property.buildings.map((building) => (
              <Box 
                key={building.id} 
                sx={{ 
                  mb: 3, 
                  bgcolor: 'background.paper',
                  borderRadius: 1,
                  boxShadow: 1,
                  position: 'relative',
                  '&:hover .building-actions': {
                    opacity: 1,
                  },
                }}
              >
                {/* Building Header */}
                <Box 
                  sx={{ 
                    p: 2, 
                    display: 'flex', 
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderBottom: 1,
                    borderColor: 'divider',
                  }}
                >
                  <Stack direction="row" spacing={1} alignItems="baseline">
                    <Typography variant="h6">
                      {building.name}
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                      ({building.rooms.reduce((total, room) => 
                        total + calculateRoomCapacity(room), 0)})
                    </Typography>
                  </Stack>
                  <Stack 
                    direction="row" 
                    spacing={1}
                    className="building-actions"
                    sx={{ 
                      opacity: 0,
                      transition: 'opacity 0.2s ease-in-out',
                    }}
                  >
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog('room', undefined, building)}
                      sx={{ 
                        bgcolor: 'background.paper',
                        '&:hover': { bgcolor: 'action.hover' },
                      }}
                    >
                      <AddIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, 'building', building)}
                      sx={{ 
                        bgcolor: 'background.paper',
                        '&:hover': { bgcolor: 'action.hover' },
                      }}
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                </Box>

                {/* Rooms List */}
                <Box sx={{ p: 2 }}>
                  <Grid container spacing={2}>
                    {building.rooms.map((room) => (
                      <Grid item xs={12} key={room.id}>
                        <Box 
                          sx={{ 
                            p: 2,
                            bgcolor: 'grey.50',
                            borderRadius: 1,
                            '&:hover': {
                              bgcolor: 'grey.100',
                            },
                            '&:hover .room-actions': {
                              opacity: 1,
                            },
                          }}
                        >
                          <Grid container alignItems="center" spacing={2}>
                            {/* Room Info */}
                            <Grid item xs={3}>
                              <Stack direction="row" spacing={1} alignItems="baseline">
                                <Typography variant="subtitle1">
                                  {room.name}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  ({calculateRoomCapacity(room)})
                                </Typography>
                              </Stack>
                              <Typography variant="body2" color="text.secondary">
                                Room {room.room_number}
                              </Typography>
                            </Grid>

                            {/* Beds */}
                            <Grid item xs={4}>
                              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                                {room.beds.map((bed) => (
                                  <Chip
                                    key={bed.id}
                                    label={formatBedInfo(bed)}
                                    size="small"
                                    variant="outlined"
                                    onDelete={() => handleDeleteBed(room.id, bed)}
                                    sx={{ 
                                      bgcolor: 'background.paper',
                                      '& .MuiChip-deleteIcon': {
                                        opacity: 0,
                                        transition: 'opacity 0.2s',
                                      },
                                      '&:hover .MuiChip-deleteIcon': {
                                        opacity: 1,
                                      },
                                    }}
                                  />
                                ))}
                                <Button
                                  size="small"
                                  startIcon={<AddIcon />}
                                  onClick={() => handleOpenDialog('bed', room)}
                                  sx={{ 
                                    minWidth: 'auto', 
                                    px: 1,
                                    height: 24,
                                    borderRadius: '12px',
                                  }}
                                >
                                  Add
                                </Button>
                              </Stack>
                            </Grid>

                            {/* Amenities */}
                            <Grid item xs={4}>
                              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                                {room.amenities && room.amenities.map((amenity, index) => (
                                  <Chip 
                                    key={index} 
                                    label={amenity} 
                                    size="small" 
                                    variant="outlined"
                                    sx={{ bgcolor: 'background.paper' }}
                                  />
                                ))}
                              </Stack>
                            </Grid>

                            {/* Actions */}
                            <Grid item xs={1}>
                              <Stack 
                                direction="row" 
                                spacing={1} 
                                justifyContent="flex-end"
                                className="room-actions"
                                sx={{ 
                                  opacity: 0,
                                  transition: 'opacity 0.2s ease-in-out',
                                }}
                              >
                                <IconButton
                                  size="small"
                                  onClick={() => handleOpenDialog('editRoom', room)}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                  size="small"
                                  onClick={() => handleOpenDialog('deleteRoom', room)}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </Stack>
                            </Grid>
                          </Grid>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              </Box>
            ))}
          </Stack>

          {/* Add/Edit Building Dialog */}
          <Dialog
            open={openDialog === 'building' || openDialog === 'editBuilding'}
            onClose={handleCloseDialog}
            aria-labelledby="building-dialog-title"
          >
            <DialogTitle id="building-dialog-title">
              {openDialog === 'editBuilding' ? 'Edit Building' : 'Add Building'}
            </DialogTitle>
            <DialogContent>
              <TextField
                autoFocus
                margin="dense"
                label="Building Name"
                type="text"
                fullWidth
                value={newBuildingName}
                onChange={(e) => setNewBuildingName(e.target.value)}
                sx={{ mt: 2 }}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button
                onClick={openDialog === 'editBuilding' ? handleEditBuilding : handleAddBuilding}
                variant="contained"
                disabled={!newBuildingName.trim()}
              >
                {openDialog === 'editBuilding' ? 'Save' : 'Add'}
              </Button>
            </DialogActions>
          </Dialog>

          {/* Add/Edit Room Dialog */}
          <Dialog
            open={openDialog === 'room' || openDialog === 'editRoom'}
            onClose={handleCloseDialog}
            aria-labelledby="room-dialog-title"
          >
            <DialogTitle id="room-dialog-title">
              {openDialog === 'editRoom' ? 'Edit Room' : 'Add Room'}
            </DialogTitle>
            <DialogContent>
              <Stack spacing={2} sx={{ mt: 1 }}>
                <TextField
                  autoFocus
                  label="Room Name"
                  type="text"
                  fullWidth
                  value={newRoomData.name}
                  onChange={(e) => setNewRoomData({ ...newRoomData, name: e.target.value })}
                />
                <TextField
                  label="Room Number"
                  type="text"
                  fullWidth
                  value={newRoomData.room_number}
                  onChange={(e) => setNewRoomData({ ...newRoomData, room_number: e.target.value })}
                />
                <TextField
                  label="Amenities"
                  type="text"
                  fullWidth
                  multiline
                  rows={2}
                  helperText="Enter amenities separated by commas"
                  value={newRoomData.amenities.join(', ')}
                  onChange={(e) => setNewRoomData({ 
                    ...newRoomData, 
                    amenities: e.target.value.split(',').map(item => item.trim()).filter(Boolean)
                  })}
                />
              </Stack>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button
                onClick={openDialog === 'editRoom' ? handleEditRoom : handleAddRoom}
                variant="contained"
                disabled={!newRoomData.name.trim() || !newRoomData.room_number.trim()}
              >
                {openDialog === 'editRoom' ? 'Save' : 'Add'}
              </Button>
            </DialogActions>
          </Dialog>

          {/* Edit Property Dialog */}
          <Dialog
            open={openDialog === 'editProperty'}
            onClose={handleCloseDialog}
            aria-labelledby="property-dialog-title"
          >
            <DialogTitle id="property-dialog-title">
              Edit Property
            </DialogTitle>
            <DialogContent>
              <Stack spacing={2} sx={{ mt: 1 }}>
                <TextField
                  autoFocus
                  label="Property Name"
                  type="text"
                  fullWidth
                  value={property.name}
                  onChange={(e) => setProperty({ ...property, name: e.target.value })}
                />
                <TextField
                  label="Property Address"
                  type="text"
                  fullWidth
                  value={property.address}
                  onChange={(e) => setProperty({ ...property, address: e.target.value })}
                />
              </Stack>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button
                onClick={handleEditProperty}
                variant="contained"
              >
                Save
              </Button>
            </DialogActions>
          </Dialog>

          {/* Context Menu */}
          <Menu
            anchorEl={menuState.element}
            open={Boolean(menuState.element)}
            onClose={handleMenuClose}
          >
            <MenuItem 
              onClick={() => handleMenuAction('edit')}
              aria-label="Edit item"
            >
              <EditIcon fontSize="small" sx={{ mr: 1 }} />
              Edit
            </MenuItem>
            <MenuItem 
              onClick={() => handleMenuAction('delete')}
              aria-label="Delete item"
            >
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              Delete
            </MenuItem>
          </Menu>

          {/* Confirmation Dialogs */}
          {/* Delete Building Confirmation Dialog */}
          <Dialog
            open={openDialog === 'deleteBuilding'}
            onClose={handleCloseDialog}
          >
            <DialogTitle>Delete Building</DialogTitle>
            <DialogContent>
              <DialogContentText>
                Are you sure you want to delete the building "{selectedBuilding?.name}"? 
                This will also delete all rooms and beds within this building. This action cannot be undone.
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button onClick={handleConfirmDeleteBuilding} color="error" variant="contained">
                Delete Building
              </Button>
            </DialogActions>
          </Dialog>

          {/* Delete Room Confirmation Dialog */}
          <Dialog
            open={openDialog === 'deleteRoom'}
            onClose={handleCloseDialog}
          >
            <DialogTitle>Delete Room</DialogTitle>
            <DialogContent>
              <DialogContentText>
                Are you sure you want to delete Room {selectedRoom?.room_number}? 
                This will also delete all beds within this room. This action cannot be undone.
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button onClick={handleConfirmDeleteRoom} color="error" variant="contained">
                Delete Room
              </Button>
            </DialogActions>
          </Dialog>

          {/* Delete Bed Confirmation Dialog */}
          <Dialog
            open={openDialog === 'deleteBed'}
            onClose={handleCloseDialog}
          >
            <DialogTitle>Delete Bed</DialogTitle>
            <DialogContent>
              <DialogContentText>
                Are you sure you want to delete this {selectedBed?.bed_type} ({selectedBed?.bed_subtype}) bed? 
                This action cannot be undone.
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button onClick={handleConfirmDeleteBed} color="error" variant="contained">
                Delete Bed
              </Button>
            </DialogActions>
          </Dialog>

          {/* Add Bed Dialog */}
          <Dialog open={openDialog === 'bed'} onClose={handleCloseDialog}>
            <DialogTitle>Add Bed to Room {selectedRoom?.room_number}</DialogTitle>
            <DialogContent>
              <Box mt={2}>
                <TextField
                  select
                  fullWidth
                  label="Bed Type"
                  value={bedType}
                  onChange={(e) => setBedType(e.target.value as BedType)}
                  margin="normal"
                >
                  {Object.values(BedType).map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  select
                  fullWidth
                  label="Bed Subtype"
                  value={bedSubtype}
                  onChange={(e) => setBedSubtype(e.target.value as BedSubType)}
                  margin="normal"
                >
                  {Object.values(BedSubType).map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </MenuItem>
                  ))}
                </TextField>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button onClick={handleAddBed} variant="contained" color="primary">
                Add Bed
              </Button>
            </DialogActions>
          </Dialog>
        </>
      ) : null}
    </Box>
  );
}
