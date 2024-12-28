import { Chip, ChipProps } from '@mui/material'

interface StatusChipProps extends Omit<ChipProps, 'color'> {
  status: 'active' | 'inactive' | 'pending' | 'cancelled'
}

export default function StatusChip({ status, ...props }: StatusChipProps) {
  const getColor = (): ChipProps['color'] => {
    switch (status) {
      case 'active':
        return 'success'
      case 'inactive':
        return 'default'
      case 'pending':
        return 'warning'
      case 'cancelled':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Chip
      {...props}
      color={getColor()}
      label={status.charAt(0).toUpperCase() + status.slice(1)}
    />
  )
}
