import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LoadingSpinner from './LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders loading spinner', () => {
    render(<LoadingSpinner />)
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toBeInTheDocument()
  })
})
