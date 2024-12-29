import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, IconButton, Typography, Button, ButtonGroup } from '@mui/material';
import { DataGrid, GridColDef, GridValueGetterParams } from '@mui/x-data-grid';
import { ChevronLeft, ChevronRight } from '@mui/icons-material';
import { format, startOfDay, addDays, subDays, eachDayOfInterval } from 'date-fns';
import { RessyApi } from '../api/core/RessyApi';
import { Room } from '../api/core/types';

const api = new RessyApi('http://localhost:8000');

interface RoomRow extends Room {
  buildingName: string;
}

interface ReservationEvent {
  id: number;
  guestName: string;
  start: Date;
  end: Date;
  roomId: number;
  roomName: string;
  roomNumber: string;
  buildingName: string;
  guestId: number;
  status: string;
}

interface GridRow {
  id: number;
  name: string;
  room_number: string;
  buildingName: string;
}

export default function ReservationGrid() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [startDate, setStartDate] = useState<Date>(startOfDay(new Date()));
  const [endDate, setEndDate] = useState<Date>(addDays(startOfDay(new Date()), 6)); // Show 7 days by default
  const [rooms, setRooms] = useState<RoomRow[]>([]);
  const [events, setEvents] = useState<ReservationEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        // First get the property to get all buildings and rooms
        const property = await api.getProperty(parseInt(id));
        
        // Flatten all rooms from all buildings
        const allRooms = property.buildings.flatMap(building => 
          building.rooms.map(room => ({
            ...room,
            buildingName: building.name,
          }))
        );
        setRooms(allRooms);

        // Get reservations
        const reservationsData = await api.getPropertyReservations(
          parseInt(id),
          format(startDate, 'yyyy-MM-dd'),
          format(endDate, 'yyyy-MM-dd')
        );

        // Log the full response to see its structure
        console.log('Full reservations response:', JSON.stringify(reservationsData, null, 2));

        // Build response
        const calendarEvents = reservationsData.reservations.map(res => {
          return {
            id: res.reservation_id,
            guestName: res.guest_name,
            start: new Date(res.start_date),
            end: new Date(res.end_date),
            roomId: res.room_id,
            roomName: res.room_name,
            roomNumber: res.room_number,
            buildingName: res.building_name,
            guestId: res.guest_id,
            status: res.status,
          };
        });
        
        setEvents(calendarEvents);
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

  // Generate dates for columns
  const dates = eachDayOfInterval({ start: startDate, end: endDate });
  
  // Create columns configuration
  const columns: GridColDef<GridRow>[] = [
    { 
      field: 'name',
      headerName: 'Room',
      width: 250,
      renderCell: (params: GridValueGetterParams<any, GridRow>) => {
        const row = params.row;
        return row ? (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              {row.buildingName}
            </Typography>
            <Typography variant="body2">
              {row.name} ({row.room_number})
            </Typography>
          </Box>
        ) : null;
      },
    },
    ...dates.map((date, index) => ({
      field: format(date, 'yyyy-MM-dd'),
      headerName: format(date, 'MMM d'),
      renderHeader: () => (
        <div>
          <div>{format(date, 'MMM d')}</div>
          <div style={{ fontSize: '0.8em', color: '#666' }}>{format(date, 'EEE')}</div>
        </div>
      ),
      cellClassName: 'reservation-cell',
      renderCell: (params: GridValueGetterParams<any, GridRow>) => {
        const reservation = events.find(event => 
          event.roomId === params.row.id && 
          format(event.start, 'yyyy-MM-dd') <= format(date, 'yyyy-MM-dd') &&
          format(event.end, 'yyyy-MM-dd') >= format(date, 'yyyy-MM-dd')
        );

        // Only render the cell content for the start date
        const isStartDate = reservation && format(reservation.start, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd');
        if (!reservation || !isStartDate) return null;

        // Calculate the number of days this reservation spans
        const startDate = reservation.start;
        const endDate = reservation.end;
        const daysDiff = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1;
        const columnIndex = dates.findIndex(d => format(d, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd'));

        const handleReservationClick = (reservation: ReservationEvent) => {
          navigate(`/reservations/${reservation.id}`);
        };

        return (
          <Box
            onClick={() => handleReservationClick(reservation)}
            sx={{
              position: 'absolute',
              left: 0,
              height: 'calc(100% - 8px)',
              width: `calc(${daysDiff * 100}% - 8px)`,
              top: '4px',
              backgroundColor: reservation.status === 'cancelled' ? '#ffebee' : '#e8f5e9',
              display: 'flex',
              alignItems: 'center',
              padding: '0 8px',
              borderRadius: '4px',
              border: '1px solid rgba(0, 0, 0, 0.12)',
              zIndex: 1,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              overflow: 'hidden',
              whiteSpace: 'nowrap',
              '&:hover': {
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                transform: 'translateY(-1px)',
              },
            }}
          >
            <Typography noWrap>
              {reservation.guestName}
            </Typography>
          </Box>
        );
      }
    }))
  ];

  // Prepare rows data
  const rows = rooms.map(room => ({
    id: room.id,
    name: room.name,
    room_number: room.room_number,
    buildingName: room.buildingName,
  }));

  if (loading && !rooms.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

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
      </Box>
      <Box sx={{ flex: 1 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          hideFooter
          disableRowSelectionOnClick
          disableColumnMenu
          rowHeight={60}
          sx={{
            '& .MuiDataGrid-cell': {
              borderRight: '1px solid rgba(224, 224, 224, 1)',
              position: 'relative',
              padding: 0,
              overflow: 'visible !important',
            },
            '& .MuiDataGrid-columnHeader': {
              borderRight: '1px solid rgba(224, 224, 224, 1)',
            },
            '& .MuiDataGrid-row': {
              position: 'relative',
            },
            '& .reservation-cell': {
              padding: 0,
              position: 'relative',
            },
          }}
        />
      </Box>
    </Box>
  );
}
