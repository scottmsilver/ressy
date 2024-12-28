import { useState, useCallback } from 'react'

interface Notification {
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

export default function useNotification() {
  const [notification, setNotification] = useState<Notification | null>(null)

  const showNotification = useCallback((message: string, type: Notification['type'] = 'info') => {
    setNotification({ message, type })
  }, [])

  const hideNotification = useCallback(() => {
    setNotification(null)
  }, [])

  return {
    notification,
    showNotification,
    hideNotification
  }
}
