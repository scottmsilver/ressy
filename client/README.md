# Ressy Client

A modern React client for the Ressy Property Management System.

## Features

- Modern, responsive UI built with Material-UI
- Type-safe development with TypeScript
- Efficient state management with React Query
- Form handling with custom hooks
- Clean and maintainable code structure

## Project Structure

```
src/
  ├── api/          # API client and types
  ├── components/   # Reusable UI components
  ├── hooks/        # Custom React hooks
  ├── pages/        # Application pages/routes
  ├── App.tsx       # Main application component
  ├── main.tsx      # Application entry point
  └── theme.ts      # Material-UI theme configuration
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Development

- The application uses Vite for fast development and building
- Material-UI for consistent and beautiful UI components
- React Query for efficient server state management
- React Router for client-side routing

## API Integration

The client communicates with the FastAPI backend running on `http://localhost:8000`. The Vite development server is configured to proxy API requests to avoid CORS issues.
