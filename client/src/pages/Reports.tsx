import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import { api } from '../api'
import type { PropertyReport, DailyReport } from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Reports() {
  const [propertyId, setPropertyId] = useState<number | ''>('')
  const [startDate, setStartDate] = useState<Date | null>(new Date())
  const [endDate, setEndDate] = useState<Date | null>(new Date())
  const [propertyReport, setPropertyReport] = useState<PropertyReport | null>(null)
  const [dailyReports, setDailyReports] = useState<DailyReport[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (propertyId && startDate && endDate) {
      fetchReports()
    }
  }, [propertyId, startDate, endDate])

  const fetchReports = async () => {
    if (!propertyId || !startDate || !endDate) return

    try {
      setLoading(true)
      const [propertyData, dailyData] = await Promise.all([
        api.getPropertyReport(Number(propertyId)),
        api.getDailyReports(Number(propertyId), startDate.toISOString(), endDate.toISOString())
      ])
      setPropertyReport(propertyData)
      setDailyReports(dailyData)
      setError(null)
    } catch (err) {
      setError('Failed to fetch reports')
      console.error('Error fetching reports:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Reports
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth>
            <InputLabel>Property</InputLabel>
            <Select
              value={propertyId}
              label="Property"
              onChange={(e) => setPropertyId(e.target.value as number)}
            >
              <MenuItem value={1}>Property 1</MenuItem>
              <MenuItem value={2}>Property 2</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={4}>
          <DatePicker
            label="Start Date"
            value={startDate}
            onChange={(date) => setStartDate(date)}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <DatePicker
            label="End Date"
            value={endDate}
            onChange={(date) => setEndDate(date)}
          />
        </Grid>
      </Grid>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {propertyReport && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Property Overview
                </Typography>
                <Typography>
                  Total Rooms: {propertyReport.totalRooms}
                </Typography>
                <Typography>
                  Available Rooms: {propertyReport.availableRooms}
                </Typography>
                <Typography>
                  Occupancy Rate: {(propertyReport.occupancyRate * 100).toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Revenue
                </Typography>
                <Typography>
                  Total Revenue: ${propertyReport.totalRevenue.toFixed(2)}
                </Typography>
                <Typography>
                  Average Daily Rate: ${propertyReport.averageDailyRate.toFixed(2)}
                </Typography>
                <Typography>
                  RevPAR: ${propertyReport.revPAR.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {dailyReports.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Daily Reports
          </Typography>
          <Grid container spacing={3}>
            {dailyReports.map((report) => (
              <Grid item xs={12} md={4} key={report.date}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      {new Date(report.date).toLocaleDateString()}
                    </Typography>
                    <Typography>
                      Occupancy: {(report.occupancyRate * 100).toFixed(1)}%
                    </Typography>
                    <Typography>
                      Revenue: ${report.revenue.toFixed(2)}
                    </Typography>
                    <Typography>
                      ADR: ${report.averageDailyRate.toFixed(2)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  )
}
