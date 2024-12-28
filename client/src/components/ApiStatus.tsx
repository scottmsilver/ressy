import { useState, useEffect } from 'react'
import { Box, Typography, Chip } from '@mui/material'
import { CheckCircle, Error } from '@mui/icons-material'
import { api, API_PORT } from '../api'

export default function ApiStatus() {
  const [isUp, setIsUp] = useState(false)
  const apiUrl = `/api (Port ${API_PORT})`

  useEffect(() => {
    const checkApiStatus = async () => {
      const isHealthy = await api.checkHealth()
      setIsUp(isHealthy)
    }

    // Check immediately
    checkApiStatus()

    // Then check every 30 seconds
    const interval = setInterval(checkApiStatus, 30000)

    return () => clearInterval(interval)
  }, [])

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Typography variant="body2" color="text.secondary">
        API:
      </Typography>
      <Chip
        size="small"
        icon={isUp ? <CheckCircle /> : <Error />}
        label={`${apiUrl} ${isUp ? 'Connected' : 'Disconnected'}`}
        color={isUp ? 'success' : 'error'}
        variant="outlined"
      />
    </Box>
  )
}
