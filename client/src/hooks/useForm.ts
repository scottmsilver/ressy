import { useState, useCallback } from 'react'

export default function useForm<T>(initialValues: T) {
  const [values, setValues] = useState<T>(initialValues)

  const handleChange = useCallback((name: keyof T) => (
    event: React.ChangeEvent<HTMLInputElement | { value: unknown }>
  ) => {
    const value = event.target.value
    setValues((prev) => ({
      ...prev,
      [name]: value,
    }))
  }, [])

  const reset = useCallback(() => {
    setValues(initialValues)
  }, [initialValues])

  return {
    values,
    handleChange,
    reset,
    setValues,
  }
}
