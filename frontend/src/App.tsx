import { useMemo, useState } from 'react'
import { alpha, ThemeProvider } from '@mui/material/styles'
import { AppBar, Box, CssBaseline, IconButton, Toolbar, Typography } from '@mui/material'
import { DarkMode, LightMode } from '@mui/icons-material'
import UploadPanel from './features/upload/UploadPanel'
import ChatWindow from './features/chat/ChatWindow'
import { buildTheme, glassSx, gradientSx } from './theme'

export default function App() {
  const [mode, setMode] = useState<'light' | 'dark'>('light')
  const theme = useMemo(() => buildTheme(mode), [mode])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          bgcolor: 'background.default',
          backgroundImage: theme =>
            `radial-gradient(circle at 15% 0%, ${alpha(
              theme.palette.primary.main,
              theme.palette.mode === 'light' ? 0.06 : 0.12
            )}, transparent 60%)`,
        }}
      >
        <AppBar
          position="static"
          elevation={0}
          sx={glassSx('0 1px 0')}
        >
          <Toolbar sx={{ justifyContent: 'space-between' }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                ...gradientSx,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              ResearchAI
            </Typography>
            <IconButton
              onClick={() => setMode(m => (m === 'light' ? 'dark' : 'light'))}
              sx={{ color: 'text.secondary' }}
            >
              {mode === 'light' ? <DarkMode /> : <LightMode />}
            </IconButton>
          </Toolbar>
        </AppBar>

        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <Box
            component="aside"
            sx={{
              width: 280,
              flexShrink: 0,
              ...glassSx('1px 0 0'),
              overflow: 'auto',
              p: 3,
            }}
          >
            <UploadPanel />
          </Box>
          <Box component="main" sx={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
            <ChatWindow />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  )
}
