import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Button, ButtonGroup, Paper } from '@mui/material';
import { DayPilot, DayPilotCalendar } from "@daypilot/daypilot-lite-react";
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

export default function ReservationGridDP() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [startDate, setStartDate] = useState<Date>(startOfDay(new Date()));
  const [endDate, setEndDate] = useState<Date>(addDays(startOfDay(new Date()), 6));
  const [loading, setLoading] = useState(true);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [calendarConfig, setCalendarConfig] = useState({
    viewType: "Resources",
    startDate: startDate.toISOString(),
    days: 7,
    cellDuration: 1440, // 24 hours in minutes
    timeHeaders: [
      { groupBy: "Day" },
      { groupBy: "Day", format: "d MMM yyyy" }
    ],
    scale: "Day",
    businessBeginsHour: 0,
    businessEndsHour: 24,
    showNonBusiness: true,
    resources: [],
    events: []
  });

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

        // Convert rooms to DayPilot resources
        const resources = allRooms.map(room => ({
          id: room.id,
          name: `${room.name} (${room.roomNumber})`,
          buildingName: room.buildingName
        }));

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

        // Convert reservations to DayPilot events
        const events = reservationsList.map(res => ({
          id: res.id,
          resource: res.roomId,
          text: res.title,
          start: new DayPilot.Date(res.start),
          end: new DayPilot.Date(res.end),
          backColor: res.status === 'cancelled' ? '#ffebee' : '#e3f2fd',
          borderColor: res.status === 'cancelled' ? '#ef5350' : '#90caf9',
          fontColor: res.status === 'cancelled' ? '#d32f2f' : '#1976d2',
          barColor: 'transparent'
        }));

        // Update calendar config
        setCalendarConfig(prev => ({
          ...prev,
          startDate: startDate.toISOString(),
          resources,
          events
        }));

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

  const handleEventClick = (args: any) => {
    const reservationId = args.e.data.id;
    navigate(`/reservations/${reservationId}`);
  };

  const handleTimeRangeSelected = (args: any) => {
    const roomId = args.resource;
    const startDate = format(new Date(args.start.value), 'yyyy-MM-dd');
    const endDate = format(new Date(args.end.value), 'yyyy-MM-dd');
    navigate(`/reservations/new?roomId=${roomId}&startDate=${startDate}&endDate=${endDate}`);
  };

  if (loading) {
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
        <Box sx={{ flex: 1 }} />
        <ButtonGroup variant="outlined" size="small">
          <Button onClick={() => navigate(`/properties/${id}/grid`)}>Grid View</Button>
          <Button onClick={() => navigate(`/properties/${id}/calendar`)}>Calendar View</Button>
        </ButtonGroup>
      </Box>
      
      <Paper sx={{ flex: 1, p: 1 }}>
        <DayPilotCalendar
          {...calendarConfig}
          onEventClick={handleEventClick}
          onTimeRangeSelected={handleTimeRangeSelected}
          height="100%"
          cellHeight={50}
          headerHeight={50}
          rowHeaderWidth={200}
          eventBarVisible={false}
          durationBarVisible={false}
          columnWidthSpec="Fixed"
          columnWidth={150}
          onBeforeEventRender={(args: any) => {
            args.data.areas = [
              {
                top: 5,
                right: 5,
                width: 16,
                height: 16,
                symbol: "triangleDown",
                fontColor: args.data.fontColor,
                visibility: "Hover",
                action: "ContextMenu",
                style: "cursor: pointer"
              }
            ];
          }}
        />
      </Paper>

      <style>
        {`
          .calendar_default_resource_inner {
            padding: 8px;
            display: flex;
            flex-direction: column;
          }
          .calendar_default_resource_inner::after {
            content: attr(data-building);
            font-size: 0.75rem;
            color: #666;
            margin-top: 2px;
          }
          .calendar_default_event_inner {
            padding: 4px 8px;
            display: flex;
            align-items: center;
            font-size: 0.875rem;
          }
        `}
      </style>
    </Box>
  );
}
