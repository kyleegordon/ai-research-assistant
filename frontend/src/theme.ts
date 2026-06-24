import { alpha, createTheme, type Theme } from '@mui/material/styles'
import { keyframes } from '@mui/system'

export const gradientSx = {
  background: 'linear-gradient(135deg, #6D28D9, #8B5CF6)',
  color: '#fff',
} as const

export const solidAccentSx = {
  bgcolor: '#6D28D9',
  color: '#fff',
} as const

export const softShadow = {
  light: '0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06)',
  dark: '0 1px 2px rgba(0, 0, 0, 0.4), 0 8px 24px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.04)',
} as const

export function glassSx(seamOffset: '0 1px 0' | '1px 0 0' | '0 -1px 0') {
  return {
    bgcolor: (theme: Theme) => alpha(theme.palette.background.paper, 0.8),
    backdropFilter: 'blur(10px)',
    boxShadow: (theme: Theme) =>
      theme.palette.mode === 'light'
        ? `${seamOffset} rgba(15, 23, 42, 0.06)`
        : `${seamOffset} rgba(0, 0, 0, 0.4)`,
  } as const
}

const shimmerSweep = keyframes`
  from { left: -60%; }
  to { left: 130%; }
`

export const shimmerSx = {
  position: 'relative',
  overflow: 'hidden',
  '&::after': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: '-60%',
    width: '40%',
    height: '100%',
    background: 'linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.55), transparent)',
    transform: 'skewX(-20deg)',
  },
  '&:hover::after': {
    animation: `${shimmerSweep} 0.9s ease`,
  },
} as const

export function buildTheme(mode: 'light' | 'dark') {
  return createTheme({
    palette: {
      mode,
      primary: { main: mode === 'light' ? '#6D28D9' : '#A78BFA' },
      secondary: { main: '#A78BFA' },
      background: {
        default: mode === 'light' ? '#F5F3FF' : '#13101F',
        paper: mode === 'light' ? '#FFFFFF' : '#1E1930',
      },
    },
    shape: { borderRadius: 12 },
    typography: {
      fontFamily:
        '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif',
      button: { fontWeight: 600 },
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: { backgroundImage: 'none' },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            transition: 'transform 0.15s ease, box-shadow 0.15s ease',
            '&:hover': { transform: 'translateY(-1px)' },
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            transition: 'box-shadow 0.15s ease, border-color 0.15s ease',
            '&.Mui-focused': {
              boxShadow: `0 0 0 3px ${
                mode === 'light' ? 'rgba(109, 40, 217, 0.15)' : 'rgba(167, 139, 250, 0.2)'
              }`,
            },
          },
        },
      },
    },
  })
}
