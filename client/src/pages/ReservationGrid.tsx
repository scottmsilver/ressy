import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Stack,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ChevronLeft, ChevronRight } from '@mui/icons-material';
import { format, addDays, eachDayOfInterval, startOfDay } from 'date-fns';
import { api } from '../api';
import type { PropertyReservation } from '../api/core/RessyApi';

interface RoomRow {
  buildingId: number;
  buildingName: string;
  roomId: number;
  roomName: string;
  roomNumber: string;
}

interface ReservationCell {
  guestId?: number;
  guestName?: string;
  status?: string;
}

export default function ReservationGrid() {
  const { id } = useParams<{ id: string }>();
  const [startDate, setStartDate] = useState<Date>(startOfDay(new Date()));
  const [endDate, setEndDate] = useState<Date>(startOfDay(addDays(new Date(), 6)));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rooms, setRooms] = useState<RoomRow[]>([]);
  const [reservations, setReservations] = useState<Map<string, ReservationCell>>(new Map());

  // Generate array of dates between start and end
  const dateRange = eachDayOfInterval({ start: startDate, end: endDate });

  useEffect(() => {
    if (!id) return;
    fetchReservations();
  }, [id, startDate, endDate]);

  const fetchReservations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // First, fetch the property to get all buildings
      const property = await api.getProperty(parseInt(id!));
      
      // Fetch all rooms for each building
      const allRooms: RoomRow[] = [];
      for (const building of property.buildings) {
        const rooms = await api.listRooms(building.id);
        rooms.forEach(room => {
          allRooms.push({
            buildingId: building.id,
            buildingName: building.name,
            roomId: room.id,
            roomName: room.name,
            roomNumber: room.room_number,
          });
        });
      }
      
      // Sort rooms by building name and room number
      setRooms(allRooms.sort((a, b) => 
        a.buildingName.localeCompare(b.buildingName) || 
        a.roomNumber.localeCompare(b.roomNumber)
      ));

      // Fetch and process reservations
      const reservationData = await api.getPropertyReservations(
        parseInt(id!),
        format(startDate, 'yyyy-MM-dd'),
        format(endDate, 'yyyy-MM-dd')
      );

      // Process reservations
      const reservationMap = new Map<string, ReservationCell>();
      reservationData.reservations.forEach((res) => {
        const start = new Date(res.start_date);
        const end = new Date(res.end_date);
        
        eachDayOfInterval({ start, end }).forEach((date) => {
          const key = `${res.room_id}-${format(date, 'yyyy-MM-dd')}`;
          reservationMap.set(key, {
            guestId: res.guest_id,
            guestName: res.guest_name,
            status: res.status,
          });
        });
      });
      setReservations(reservationMap);
    } catch (err) {
      console.error('Error fetching reservations:', err);
      setError('Failed to fetch reservations');
    } finally {
      setLoading(false);
    }
  };

  const handlePreviousWeek = () => {
    setStartDate(prev => addDays(prev, -7));
    setEndDate(prev => addDays(prev, -7));
  };

  const handleNextWeek = () => {
    setStartDate(prev => addDays(prev, 7));
    setEndDate(prev => addDays(prev, 7));
  };

  const getCellColor = (reservation?: ReservationCell): string => {
    if (!reservation) return '#ffffff'; // Available
    if (reservation.status === 'cancelled') return '#ffebee'; // Light red
    return '#e8f5e9'; // Light green for occupied
  };

  if (loading && !rooms.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
        <IconButton onClick={handlePreviousWeek}>
          <ChevronLeft />
        </IconButton>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DatePicker
            label="Start Date"
            value={startDate}
            onChange={(date) => date && setStartDate(startOfDay(date))}
          />
          <Typography sx={{ mx: 1 }}>to</Typography>
          <DatePicker
            label="End Date"
            value={endDate}
            onChange={(date) => date && setEndDate(startOfDay(date))}
          />
        </LocalizationProvider>
        <IconButton onClick={handleNextWeek}>
          <ChevronRight />
        </IconButton>
      </Stack>

      <TableContainer component={Paper}>
        <Table size="small" sx={{ minWidth: 800 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Room</TableCell>
              {dateRange.map((date) => (
                <TableCell 
                  key={date.toISOString()} 
                  align="center"
                  sx={{ 
                    fontWeight: 'bold',
                    minWidth: 120,
                    bgcolor: 'grey.100'
                  }}
                >
                  {format(date, 'MMM d')}
                  <Typography variant="caption" display="block" color="text.secondary">
                    {format(date, 'EEE')}
                  </Typography>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rooms.map((room) => (
              <TableRow key={room.roomId}>
                <TableCell 
                  component="th" 
                  scope="row"
                  sx={{ 
                    bgcolor: 'grey.50',
                    borderRight: 1,
                    borderColor: 'divider'
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    {room.buildingName}
                  </Typography>
                  <Typography>
                    {room.roomName} ({room.roomNumber})
                  </Typography>
                </TableCell>
                {dateRange.map((date) => {
                  const key = `${room.roomId}-${format(date, 'yyyy-MM-dd')}`;
                  const reservation = reservations.get(key);
                  return (
                    <TableCell 
                      key={key}
                      align="center"
                      sx={{ 
                        bgcolor: getCellColor(reservation),
                        '&:hover': {
                          bgcolor: 'action.hover',
                        },
                      }}
                    >
                      {reservation?.guestName && (
                        <Typography variant="body2">
                          {reservation.guestName}
                        </Typography>
                      )}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
