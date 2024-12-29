import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, IconButton, Typography, Button, ButtonGroup, Dialog } from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { ChevronLeft, ChevronRight } from '@mui/icons-material';
import { format, startOfDay, addDays, subDays, eachDayOfInterval, isWithinInterval, differenceInDays, parseISO } from 'date-fns';
import { RessyApi } from '../api/core/RessyApi';
import { Room } from '../api/core/types';
import { createPortal } from 'react-dom';

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

interface DragState {
  active: boolean;
  startDate: Date | null;
  endDate: Date | null;
  roomId: number | null;
}

export default function ReservationGrid() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [startDate, setStartDate] = useState<Date>(startOfDay(new Date()));
  const [endDate, setEndDate] = useState<Date>(addDays(startOfDay(new Date()), 6)); // Show 7 days by default
  const [rooms, setRooms] = useState<RoomRow[]>([]);
  const [reservations, setReservations] = useState<ReservationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragState, setDragState] = useState<DragState>({
    active: false,
    startDate: null,
    endDate: null,
    roomId: null
  });
  const [showReservationDialog, setShowReservationDialog] = useState(false);

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
          const startDate = new Date(res.start_date);
          const endDate = new Date(res.end_date);
          
          // Set check-in time to 3 PM (15:00)
          startDate.setHours(15, 0, 0);
          
          // Set check-out time to 11:59:59 PM to include the full end date
          endDate.setHours(23, 59, 59);
          
          return {
            id: res.reservation_id,
            guestName: res.guest_name,
            start: startDate,
            end: endDate,
            roomId: res.room_id,
            roomName: res.room_name,
            roomNumber: res.room_number,
            buildingName: res.building_name,
            guestId: res.guest_id,
            status: res.status,
          };
        });
        
        setReservations(calendarEvents);
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
      renderCell: (params: GridRenderCellParams<any, GridRow>) => {
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
      renderCell: (params: GridRenderCellParams) => {
        const date = new Date(params.field);
        const matchingReservations = reservations.filter(event => 
          event.roomId === params.row.id && 
          format(event.start, 'yyyy-MM-dd') <= format(date, 'yyyy-MM-dd') &&
          format(event.end, 'yyyy-MM-dd') >= format(date, 'yyyy-MM-dd')
        );

        const isDragging = dragState.active && dragState.roomId === params.row.id;
        const isInDragRange = isDragging && dragState.startDate && dragState.endDate && 
          isWithinInterval(date, {
            start: startOfDay(dragState.startDate),
            end: startOfDay(dragState.endDate)
          });

        return (
          <>
            {matchingReservations.map(reservation => {
              const isStartDate = format(reservation.start, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd');
              const isEndDate = format(reservation.end, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd');
              
              return (
                <Box
                  key={reservation.id}
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    navigate(`/reservations/${reservation.id}`);
                  }}
                  sx={{
                    position: 'absolute',
                    left: 0,
                    top: '20%',
                    height: '60%',
                    width: '100%',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    zIndex: 1000,
                    pointerEvents: 'auto',
                    '&:hover': {
                      '& .reservation-overlay': {
                        backgroundColor: 'rgba(0, 0, 0, 0.05)',
                      }
                    },
                  }}
                >
                  {/* Transparent overlay for hover and click */}
                  <Box
                    className="reservation-overlay"
                    sx={{
                      position: 'absolute',
                      left: isStartDate ? '50%' : 0,
                      right: isEndDate ? '50%' : 0,
                      top: 0,
                      bottom: 0,
                      backgroundColor: 'transparent',
                      borderTop: `1px solid ${reservation.status === 'cancelled' ? '#ef5350' : '#90caf9'}`,
                      borderBottom: `1px solid ${reservation.status === 'cancelled' ? '#ef5350' : '#90caf9'}`,
                      borderLeft: isStartDate ? `1px solid ${reservation.status === 'cancelled' ? '#ef5350' : '#90caf9'}` : 'none',
                      borderRight: isEndDate ? `1px solid ${reservation.status === 'cancelled' ? '#ef5350' : '#90caf9'}` : 'none',
                      transition: 'background-color 0.2s',
                    }}
                  />
                  
                  {/* Visible label only on start date */}
                  {isStartDate && (
                    <Box
                      sx={{
                        position: 'absolute',
                        left: '50%',
                        right: 0,
                        top: 0,
                        bottom: 0,
                        backgroundColor: reservation.status === 'cancelled' ? '#ffebee' : '#e3f2fd',
                        border: '1px solid',
                        borderColor: reservation.status === 'cancelled' ? '#ef5350' : '#90caf9',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        padding: '4px 8px',
                        overflow: 'hidden',
                        pointerEvents: 'none', // Let clicks go through to the overlay
                        // Extend beyond the cell
                        width: `${(differenceInDays(new Date(reservation.end), date) + 1) * 100}%`,
                      }}
                    >
                      <Typography noWrap>
                        {reservation.guestName}
                      </Typography>
                    </Box>
                  )}
                </Box>
              );
            })}
            {isInDragRange && (
              <Box
                sx={{
                  position: 'absolute',
                  left: format(date, 'yyyy-MM-dd') === format(dragState.startDate!, 'yyyy-MM-dd') ? '50%' : 0,
                  right: format(date, 'yyyy-MM-dd') === format(dragState.endDate!, 'yyyy-MM-dd') ? '50%' : 0,
                  top: '20%',
                  height: '60%',
                  backgroundColor: 'rgba(144, 202, 249, 0.2)',
                  border: '2px dashed #90caf9',
                  borderRadius: '4px',
                  pointerEvents: 'none',
                }}
              />
            )}
          </>
        );
      }
    }))
  ];

  const handleCellMouseDown = (params: GridRenderCellParams) => {
    if (params.field === 'name') return;
    
    setDragState({
      active: true,
      startDate: parseISO(params.field as string),
      endDate: parseISO(params.field as string),
      roomId: params.row.id
    });
  };

  const handleCellMouseEnter = (params: GridRenderCellParams) => {
    if (!dragState.active || params.field === 'name' || params.row.id !== dragState.roomId) return;

    const currentDate = parseISO(params.field as string);
    setDragState(prev => ({
      ...prev,
      endDate: currentDate
    }));
  };

  const handleCellMouseUp = () => {
    if (!dragState.active || !dragState.startDate || !dragState.endDate) return;

    // Ensure start date is before end date
    const finalStartDate = dragState.startDate < dragState.endDate ? dragState.startDate : dragState.endDate;
    const finalEndDate = dragState.startDate < dragState.endDate ? dragState.endDate : dragState.startDate;

    // Navigate to new reservation page with pre-populated dates
    navigate(`/reservations/new?roomId=${dragState.roomId}&startDate=${format(finalStartDate, 'yyyy-MM-dd')}&endDate=${format(finalEndDate, 'yyyy-MM-dd')}`);

    setDragState({
      active: false,
      startDate: null,
      endDate: null,
      roomId: null
    });
  };

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

  const numDays = dates.length;

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
      <Box sx={{ flex: 1 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          hideFooter
          disableRowSelectionOnClick
          disableColumnMenu
          rowHeight={60}
          onCellMouseDown={(params) => handleCellMouseDown(params)}
          onCellMouseEnter={(params) => handleCellMouseEnter(params)}
          onCellMouseUp={handleCellMouseUp}
          sx={{
            '& .MuiDataGrid-cell': {
              borderRight: '1px solid rgba(224, 224, 224, 1)',
              position: 'relative',
              padding: 0,
              overflow: 'visible !important',
              cursor: 'pointer',
              zIndex: 1,
              userSelect: 'none',
              '& > *': {
                overflow: 'visible !important',
                position: 'relative',
                '&:before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  pointerEvents: 'none'
                }
              }
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
