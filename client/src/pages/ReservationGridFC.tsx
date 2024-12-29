import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Button, ButtonGroup, Paper } from '@mui/material';
import { format, startOfDay, addDays } from 'date-fns';
import { RessyApi } from '../api/core/RessyApi';

const api = new RessyApi('http://localhost:8000');

interface Room {
  id: string;
  name: string;
  roomNumber: string;
  buildingName: string;
}

interface Reservation {
  id: string;
  roomId: string;
  title: string;
  start: string;
  end: string;
  status: string;
  guestId: number;
  buildingName: string;
  roomName: string;
}

export default function ReservationGridFC() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [startDate, setStartDate] = useState<Date>(startOfDay(new Date()));
  const [endDate, setEndDate] = useState<Date>(addDays(startOfDay(new Date()), 6));
  const [loading, setLoading] = useState(true);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [selectedCells, setSelectedCells] = useState<{start?: Date; end?: Date; roomId?: string}>({});
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!id) return;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        // First get the property to get all buildings and rooms
        const property = await api.getProperty(parseInt(id));
        
        // Flatten rooms with building info
        const allRooms = property.buildings.flatMap(building => 
          building.rooms.map(room => ({
            id: room.id.toString(),
            name: room.name,
            roomNumber: room.room_number,
            buildingName: building.name
          }))
        );
        setRooms(allRooms);

        // Get reservations
        const reservationsData = await api.getPropertyReservations(
          parseInt(id),
          format(startDate, 'yyyy-MM-dd'),
          format(endDate, 'yyyy-MM-dd')
        );

        setReservations(reservationsData.reservations.map(res => ({
          id: res.reservation_id.toString(),
          roomId: res.room_id.toString(),
          title: res.guest_name,
          start: res.start_date,
          end: res.end_date,
          status: res.status,
          guestId: res.guest_id,
          buildingName: res.building_name,
          roomName: res.room_name
        })));
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, startDate, endDate]);

  const moveDates = (days: number) => {
    setStartDate(prev => addDays(prev, days));
    setEndDate(prev => addDays(prev, days));
  };

  const getDates = () => {
    const dates: Date[] = [];
    let currentDate = startDate;
    while (currentDate <= endDate) {
      dates.push(currentDate);
      currentDate = addDays(currentDate, 1);
    }
    return dates;
  };

  const handleCellMouseDown = (date: Date, roomId: string) => {
    setIsDragging(true);
    setSelectedCells({ start: date, end: date, roomId });
  };

  const handleCellMouseEnter = (date: Date, roomId: string) => {
    if (isDragging && selectedCells.roomId === roomId) {
      setSelectedCells(prev => ({
        ...prev,
        end: date
      }));
    }
  };

  const handleCellMouseUp = () => {
    if (selectedCells.start && selectedCells.end && selectedCells.roomId) {
      const startDate = format(selectedCells.start, 'yyyy-MM-dd');
      const endDate = format(selectedCells.end, 'yyyy-MM-dd');
      navigate(`/reservations/new?roomId=${selectedCells.roomId}&startDate=${startDate}&endDate=${endDate}`);
    }
    setIsDragging(false);
    setSelectedCells({});
  };

  const handleReservationClick = (reservationId: string) => {
    navigate(`/reservations/${reservationId}`);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  const dates = getDates();

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', p: 2, display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 2 }}>
        <ButtonGroup variant="outlined" size="small">
          <Button onClick={() => moveDates(-3)}>-3 Days</Button>
          <Button onClick={() => moveDates(-7)}>-Week</Button>
          <Button onClick={() => moveDates(7)}>+Week</Button>
          <Button onClick={() => moveDates(3)}>+3 Days</Button>
        </ButtonGroup>
        <Typography>
          {format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')}
        </Typography>
        <Box sx={{ flex: 1 }} />
        <Button
          variant="outlined"
          size="small"
          onClick={() => navigate(`/properties/${id}/grid`)}
        >
          Switch to Grid View
        </Button>
      </Box>
      
      <Paper sx={{ flex: 1, overflow: 'auto' }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'auto 1fr', height: '100%', overflow: 'hidden' }}>
          {/* Room Column */}
          <Box sx={{ 
            borderRight: '1px solid rgba(224, 224, 224, 1)',
            bgcolor: 'background.paper',
            position: 'sticky',
            left: 0,
            zIndex: 2,
            boxShadow: '2px 0 4px rgba(0,0,0,0.1)'
          }}>
            {/* Header Cell */}
            <Box sx={{ 
              height: 50,
              borderBottom: '1px solid rgba(224, 224, 224, 1)',
              p: 1,
              bgcolor: 'grey.100',
              display: 'flex',
              alignItems: 'center'
            }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Rooms</Typography>
            </Box>
            {/* Room Cells */}
            {rooms.map(room => (
              <Box 
                key={room.id}
                sx={{ 
                  p: 1,
                  borderBottom: '1px solid rgba(224, 224, 224, 1)',
                  height: 100,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {room.name} ({room.roomNumber})
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {room.buildingName}
                </Typography>
              </Box>
            ))}
          </Box>

          {/* Calendar Grid */}
          <Box sx={{ overflow: 'auto' }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: `repeat(${dates.length}, 1fr)` }}>
              {/* Date Headers */}
              {dates.map(date => (
                <Box 
                  key={date.toISOString()} 
                  sx={{ 
                    height: 50,
                    borderBottom: '1px solid rgba(224, 224, 224, 1)',
                    borderRight: '1px solid rgba(224, 224, 224, 1)',
                    p: 1,
                    bgcolor: 'grey.100',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: 500 }}>
                    {format(date, 'EEE')}
                  </Typography>
                  <Typography variant="caption">
                    {format(date, 'MMM d')}
                  </Typography>
                </Box>
              ))}

              {/* Grid Cells */}
              {rooms.map(room => (
                <React.Fragment key={room.id}>
                  {dates.map(date => {
                    const isSelected = selectedCells.roomId === room.id && 
                      date >= (selectedCells.start || date) && 
                      date <= (selectedCells.end || date);
                    
                    const reservation = reservations.find(r => 
                      r.roomId === room.id && 
                      new Date(r.start) <= date && 
                      new Date(r.end) > date
                    );

                    return (
                      <Box
                        key={date.toISOString()}
                        sx={{
                          height: 100,
                          borderBottom: '1px solid rgba(224, 224, 224, 1)',
                          borderRight: '1px solid rgba(224, 224, 224, 1)',
                          bgcolor: isSelected ? 'action.selected' : 'background.paper',
                          cursor: 'pointer',
                          position: 'relative',
                          '&:hover': {
                            bgcolor: isSelected ? 'action.selected' : 'action.hover'
                          }
                        }}
                        onMouseDown={() => handleCellMouseDown(date, room.id)}
                        onMouseEnter={() => handleCellMouseEnter(date, room.id)}
                        onMouseUp={handleCellMouseUp}
                      >
                        {reservation && (
                          <Box
                            onClick={() => handleReservationClick(reservation.id)}
                            sx={{
                              position: 'absolute',
                              top: '50%',
                              left: 4,
                              right: 4,
                              transform: 'translateY(-50%)',
                              p: 1,
                              borderRadius: 1,
                              bgcolor: reservation.status === 'cancelled' ? '#ffebee' : '#e3f2fd',
                              border: `1px solid ${reservation.status === 'cancelled' ? '#ef5350' : '#90caf9'}`,
                              cursor: 'pointer',
                              '&:hover': {
                                filter: 'brightness(0.95)'
                              }
                            }}
                          >
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                display: 'block',
                                color: reservation.status === 'cancelled' ? '#d32f2f' : '#1976d2',
                                fontWeight: 500,
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis'
                              }}
                            >
                              {reservation.title}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    );
                  })}
                </React.Fragment>
              ))}
            </Box>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
