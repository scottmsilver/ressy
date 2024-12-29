import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Button, ButtonGroup, Paper } from '@mui/material';
import { format, startOfDay, addDays, eachDayOfInterval } from 'date-fns';
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

export default function ReservationGridRC() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [startDate, setStartDate] = useState<Date>(startOfDay(new Date()));
  const [endDate, setEndDate] = useState<Date>(addDays(startOfDay(new Date()), 6));
  const [loading, setLoading] = useState(true);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [selectedCell, setSelectedCell] = useState<{ roomId?: string; date?: Date }>({});

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

        const reservationsList = reservationsData.reservations.map(res => ({
          id: res.reservation_id.toString(),
          roomId: res.room_id.toString(),
          title: res.guest_name,
          start: res.start_date,
          end: res.end_date,
          status: res.status,
          guestId: res.guest_id,
          buildingName: res.building_name,
          roomName: res.room_name
        }));
        setReservations(reservationsList);
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

  const handleCellClick = (roomId: string, date: Date) => {
    if (selectedCell.roomId === roomId && selectedCell.date?.getTime() === date.getTime()) {
      navigate(`/reservations/new?roomId=${roomId}&startDate=${format(date, 'yyyy-MM-dd')}&endDate=${format(addDays(date, 1), 'yyyy-MM-dd')}`);
    } else {
      setSelectedCell({ roomId, date });
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  const days = eachDayOfInterval({ start: startDate, end: endDate });

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
        <ButtonGroup variant="outlined" size="small">
          <Button onClick={() => navigate(`/properties/${id}/grid`)}>Grid View</Button>
          <Button onClick={() => navigate(`/properties/${id}/calendar`)}>Calendar View</Button>
          <Button onClick={() => navigate(`/properties/${id}/daypilot`)}>DayPilot View</Button>
          <Button onClick={() => navigate(`/properties/${id}/react-calendar`)}>React Calendar</Button>
        </ButtonGroup>
      </Box>
      
      <Paper sx={{ flex: 1, p: 1, overflow: 'auto' }}>
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: 'minmax(200px, auto) repeat(7, 1fr)', 
          gap: 1,
        }}>
          {/* Header row */}
          <Box sx={{ 
            p: 1, 
            bgcolor: 'grey.100', 
            borderBottom: 1, 
            borderColor: 'divider',
            fontWeight: 'bold'
          }}>
            Room
          </Box>
          {days.map(day => (
            <Box key={day.toISOString()} sx={{ 
              p: 1, 
              bgcolor: 'grey.100', 
              borderBottom: 1, 
              borderColor: 'divider',
              fontWeight: 'bold',
              textAlign: 'center'
            }}>
              {format(day, 'EEE')}<br />
              {format(day, 'MMM d')}
            </Box>
          ))}

          {/* Room rows */}
          {rooms.map(room => (
            <Box 
              key={room.id}
              sx={{
                display: 'grid',
                gridTemplateColumns: 'subgrid',
                gridColumn: '1 / -1',
                minHeight: '40px',
                position: 'relative'
              }}
            >
              {/* Room name cell */}
              <Box sx={{ 
                p: 0.5, 
                borderBottom: 1, 
                borderColor: 'divider',
                bgcolor: 'grey.50'
              }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.875rem' }}>{room.name}</Typography>
                <Typography variant="caption" sx={{ fontSize: '0.75rem' }} color="text.secondary">{room.buildingName}</Typography>
              </Box>

              {/* Day cells */}
              {days.map(day => (
                <Box 
                  key={day.toISOString()}
                  onClick={() => handleCellClick(room.id, day)}
                  sx={{ 
                    borderBottom: 1,
                    borderColor: 'divider',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'action.hover'
                    }
                  }}
                />
              ))}

              {/* Reservations */}
              {reservations
                .filter(res => res.roomId === room.id)
                .map(res => {
                  const start = new Date(res.start);
                  const end = new Date(res.end);
                  const startIndex = days.findIndex(day => startOfDay(day).getTime() === startOfDay(start).getTime());
                  const endIndex = days.findIndex(day => startOfDay(day).getTime() === startOfDay(end).getTime());
                  
                  // Skip if reservation is completely outside visible range
                  if (startIndex === -1 && endIndex === -1) return null;
                  
                  const visibleStartIndex = Math.max(0, startIndex);
                  const visibleEndIndex = endIndex === -1 ? days.length - 1 : endIndex;
                  
                  // Calculate position and width
                  const dayWidth = `calc((100% - 200px) / ${days.length})`;
                  const startOffset = startIndex < 0 ? 0 : 0.5;
                  const endOffset = endIndex >= days.length || endIndex === -1 ? 0 : 0.5;
                  
                  const left = `calc(200px + (${visibleStartIndex} * ${dayWidth}) + (${startOffset} * ${dayWidth}))`;
                  const width = `calc(((${visibleEndIndex - visibleStartIndex + 1} - ${startOffset + endOffset}) * ${dayWidth}))`;
                  
                  return (
                    <Box
                      key={res.id}
                      onClick={() => navigate(`/reservations/${res.id}`)}
                      sx={{
                        position: 'absolute',
                        top: '6px',
                        left,
                        width,
                        height: 'calc(100% - 12px)',
                        p: 0.5,
                        borderRadius: 1,
                        bgcolor: res.status === 'cancelled' ? '#ffebee' : '#e3f2fd',
                        color: res.status === 'cancelled' ? '#d32f2f' : '#1976d2',
                        border: 1,
                        borderColor: res.status === 'cancelled' ? '#ef9a9a' : '#90caf9',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        overflow: 'hidden',
                        whiteSpace: 'nowrap',
                        textOverflow: 'ellipsis',
                        zIndex: 1,
                        '&:hover': {
                          filter: 'brightness(0.95)'
                        },
                        '&::before': startIndex < 0 ? {
                          content: '"←"',
                          position: 'absolute',
                          left: 4,
                          top: '50%',
                          transform: 'translateY(-50%)'
                        } : undefined,
                        '&::after': endIndex >= days.length || endIndex === -1 ? {
                          content: '"→"',
                          position: 'absolute',
                          right: 4,
                          top: '50%',
                          transform: 'translateY(-50%)'
                        } : undefined
                      }}
                    >
                      <Box sx={{ 
                        ml: startIndex < 0 ? 3 : 0,
                        mr: endIndex >= days.length || endIndex === -1 ? 3 : 0,
                        flex: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}>
                        {res.title}
                      </Box>
                    </Box>
                  );
                })}
            </Box>
          ))}
        </Box>
      </Paper>
    </Box>
  );
}
