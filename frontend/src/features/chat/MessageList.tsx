import { Box, Paper, Typography } from '@mui/material'
import { ChatBubbleOutlined } from '@mui/icons-material'
import { keyframes } from '@mui/system'
import type { Message } from './ChatWindow'
import { gradientSx } from '../../theme'

const bounce = keyframes`
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-4px); opacity: 1; }
`

export default function MessageList({ messages }: { messages: Message[] }) {
  return (
    <Box
      sx={{
        flex: 1,
        overflowY: 'auto',
        p: 3,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.length === 0 && (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1.5,
            color: 'text.secondary',
          }}
        >
          <ChatBubbleOutlined sx={{ fontSize: 48, opacity: 0.3 }} />
          <Typography variant="body2" sx={{ textAlign: 'center' }}>
            Upload a document and ask a question.
          </Typography>
        </Box>
      )}
      {messages.map((msg, i) => (
        <Box
          key={i}
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}
        >
          <Typography variant="caption" sx={{ mb: 0.5, px: 1, color: 'text.secondary' }}>
            {msg.role === 'user' ? 'You' : 'Assistant'}
          </Typography>
          <Paper
            elevation={0}
            sx={
              msg.role === 'user'
                ? {
                    ...gradientSx,
                    maxWidth: '75%',
                    px: 2,
                    py: 1.25,
                    borderRadius: '18px 18px 4px 18px',
                  }
                : {
                    maxWidth: '75%',
                    px: 2,
                    py: 1.25,
                    borderRadius: '18px 18px 18px 4px',
                    bgcolor: 'background.paper',
                    border: 1,
                    borderColor: 'divider',
                  }
            }
          >
            {msg.content === '' ? (
              <Box sx={{ display: 'flex', gap: 0.5, py: 0.5 }}>
                {[0, 1, 2].map(dot => (
                  <Box
                    key={dot}
                    sx={{
                      width: 7,
                      height: 7,
                      borderRadius: '50%',
                      bgcolor: 'text.secondary',
                      animation: `${bounce} 1.4s ease-in-out infinite`,
                      animationDelay: `${dot * 0.16}s`,
                    }}
                  />
                ))}
              </Box>
            ) : (
              <Typography variant="body2" sx={{ lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </Typography>
            )}
          </Paper>
        </Box>
      ))}
    </Box>
  )
}
