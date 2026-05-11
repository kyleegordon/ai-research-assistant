import { useMemo, useState } from 'react'
import { ThemeProvider } from '@mui/material/styles'
import { AppBar, Box, CssBaseline, IconButton, Toolbar, Typography } from '@mui/material'
import { DarkMode, LightMode } from '@mui/icons-material'
import UploadPanel from './features/upload/UploadPanel'
import ChatWindow from './features/chat/ChatWindow'
import { buildTheme } from './theme'

export default function App() {
  const [mode, setMode] = useState<'light' | 'dark'>('light')
  const theme = useMemo(() => buildTheme(mode), [mode])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <AppBar
          position="static"
          elevation={0}
          sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}
        >
          <Toolbar sx={{ justifyContent: 'space-between' }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #7C3AED, #2563EB)',
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
              borderRight: 1,
              borderColor: 'divider',
              bgcolor: 'background.paper',
              overflow: 'auto',
              p: 2.5,
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
