import { Grid, Typography, Button } from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'

interface PageHeaderProps {
  title: string
  onAdd?: () => void
  addButtonText?: string
}

export default function PageHeader({
  title,
  onAdd,
  addButtonText = 'Add New',
}: PageHeaderProps) {
  return (
    <Grid container spacing={2} alignItems="center" sx={{ mb: 3 }}>
      <Grid item>
        <Typography variant="h4">{title}</Typography>
      </Grid>
      {onAdd && (
        <Grid item>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={onAdd}
          >
            {addButtonText}
          </Button>
        </Grid>
      )}
    </Grid>
  )
}
