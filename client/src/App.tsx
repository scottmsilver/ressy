import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Properties from './pages/Properties'
import PropertyDetails from './pages/PropertyDetails'
import Guests from './pages/Guests'
import Reservations from './pages/Reservations'
import Reports from './pages/Reports'
import ReservationGrid from './pages/ReservationGrid'
import ReservationDetails from './pages/ReservationDetails'

function App() {
  return (
    <Box sx={{ display: 'flex' }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="properties" element={<Properties />} />
          <Route path="properties/:id" element={<PropertyDetails />} />
          <Route path="properties/:id/grid" element={<ReservationGrid />} />
          <Route path="properties/:id/reservations" element={<ReservationGrid />} /> {/* Add this for backward compatibility */}
          <Route path="guests" element={<Guests />} />
          <Route path="reservations" element={<Reservations />} />
          <Route path="reservations/:id" element={<ReservationDetails />} />
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </Box>
  )
}

export default App
