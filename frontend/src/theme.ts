import { createTheme } from '@mui/material/styles'

export const gradientSx = {
  background: 'linear-gradient(135deg, #7C3AED, #2563EB)',
  color: '#fff',
} as const

export function buildTheme(mode: 'light' | 'dark') {
  return createTheme({
    palette: {
      mode,
      primary: { main: '#6D28D9' },
      secondary: { main: '#A78BFA' },
      background: {
        default: mode === 'light' ? '#F5F3FF' : '#0F172A',
        paper: mode === 'light' ? '#FFFFFF' : '#1E1E2E',
      },
    },
    shape: { borderRadius: 12 },
    typography: {
      fontFamily: '"Inter", system-ui, sans-serif',
    },
  })
}
