import { Snackbar, Alert } from '@mui/material'

interface NotificationProps {
  open: boolean
  message: string
  type?: 'success' | 'error' | 'info' | 'warning'
  onClose: () => void
}

export default function Notification({
  open,
  message,
  type = 'info',
  onClose,
}: NotificationProps) {
  return (
    <Snackbar
      open={open}
      autoHideDuration={6000}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    >
      <Alert onClose={onClose} severity={type} sx={{ width: '100%' }}>
        {message}
      </Alert>
    </Snackbar>
  )
}
