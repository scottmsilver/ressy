import { Alert, AlertTitle } from '@mui/material'

interface ErrorAlertProps {
  title?: string
  message: string
}

export default function ErrorAlert({ title = 'Error', message }: ErrorAlertProps) {
  return (
    <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
      <AlertTitle>{title}</AlertTitle>
      {message}
    </Alert>
  )
}
