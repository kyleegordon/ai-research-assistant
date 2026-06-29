import { useMemo, useRef, useState } from 'react'
import { alpha, ThemeProvider } from '@mui/material/styles'
import { AppBar, Box, Button, CssBaseline, IconButton, Toolbar, Typography } from '@mui/material'
import { ChevronLeft, ChevronRight, DarkMode, LightMode } from '@mui/icons-material'
import UploadPanel from './features/upload/UploadPanel'
import ChatWindow from './features/chat/ChatWindow'
import { buildTheme, glassSx, gradientSx } from './theme'

export default function App() {
  const [mode, setMode] = useState<'light' | 'dark'>('light')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const theme = useMemo(() => buildTheme(mode), [mode])
  const clearChatRef = useRef<() => void>(() => {})

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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => clearChatRef.current()}
                sx={{ color: 'text.secondary', borderColor: 'text.secondary' }}
              >
                Clear Chat
              </Button>
              <IconButton
                onClick={() => setMode(m => (m === 'light' ? 'dark' : 'light'))}
                sx={{ color: 'text.secondary' }}
              >
                {mode === 'light' ? <DarkMode /> : <LightMode />}
              </IconButton>
            </Box>
          </Toolbar>
        </AppBar>

        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <Box
            component="aside"
            sx={{
              width: sidebarOpen ? 280 : 0,
              flexShrink: 0,
              ...glassSx('1px 0 0'),
              overflow: 'hidden',
              transition: 'width 0.2s ease',
            }}
          >
            <Box sx={{ width: 280, overflow: 'auto', p: 3, height: '100%' }}>
              <UploadPanel />
            </Box>
          </Box>
          <Box sx={{ position: 'relative', display: 'flex', alignItems: 'center', width: 16, flexShrink: 0 }}>
            <IconButton
              size="small"
              onClick={() => setSidebarOpen(o => !o)}
              sx={{
                position: 'absolute',
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 1,
                bgcolor: 'background.paper',
                border: theme => `1px solid ${theme.palette.divider}`,
                width: 24,
                height: 24,
                color: 'text.secondary',
                '&:hover': { bgcolor: 'action.hover' },
              }}
            >
              {sidebarOpen ? <ChevronLeft sx={{ fontSize: 16 }} /> : <ChevronRight sx={{ fontSize: 16 }} />}
            </IconButton>
          </Box>
          <Box component="main" sx={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
            <ChatWindow clearChatRef={clearChatRef} />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  )
}
