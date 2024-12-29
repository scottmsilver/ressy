import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  IconButton,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import { RessyApi } from '../api/core/RessyApi';
import LoadingSpinner from '../components/LoadingSpinner';
import type { Reservation } from '../api/core/types';

const api = new RessyApi('http://localhost:8000');

export default function ReservationDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReservation = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const data = await api.getReservation(parseInt(id));
        setReservation(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching reservation:', err);
        setError('Failed to load reservation details');
      } finally {
        setLoading(false);
      }
    };

    fetchReservation();
  }, [id]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error || !reservation) {
    return (
      <Box p={2}>
        <Typography color="error">{error || 'Reservation not found'}</Typography>
      </Box>
    );
  }

  return (
    <Box p={2}>
      <Box display="flex" alignItems="center" mb={2}>
        <IconButton onClick={() => navigate(-1)} sx={{ mr: 1 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5">Reservation Details</Typography>
      </Box>

      <Card>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h6">
                  {reservation.guest_name}
                </Typography>
                <Chip
                  label={reservation.status}
                  color={reservation.status === 'cancelled' ? 'error' : 'success'}
                />
              </Box>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Check-in
              </Typography>
              <Typography>
                {format(new Date(reservation.start_date), 'PPP')}
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Check-out
              </Typography>
              <Typography>
                {format(new Date(reservation.end_date), 'PPP')}
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" color="textSecondary">
                Room Details
              </Typography>
              <Typography>
                {reservation.building_name} - {reservation.room_name} ({reservation.room_number})
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" color="textSecondary">
                Guest Contact
              </Typography>
              <Typography>
                {reservation.guest_email || 'No email provided'}
              </Typography>
              <Typography>
                {reservation.guest_phone || 'No phone provided'}
              </Typography>
            </Grid>

            {reservation.notes && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="textSecondary">
                  Notes
                </Typography>
                <Typography>
                  {reservation.notes}
                </Typography>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}
