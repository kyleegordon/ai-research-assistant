import { useEffect, useRef } from 'react'
import { Avatar, Box, Paper, Typography } from '@mui/material'
import { alpha, type Theme } from '@mui/material/styles'
import { ChatBubbleOutlined, Person, SmartToy } from '@mui/icons-material'
import { keyframes } from '@mui/system'
import type { Message } from './ChatWindow'
import { softShadow, solidAccentSx } from '../../theme'
import CopyButton from './CopyButton'
import MarkdownContent from './MarkdownContent'

const bounce = keyframes`
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-4px); opacity: 1; }
`

const fadeSlideIn = keyframes`
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
`

export default function MessageList({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

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
      {messages.map((msg, i) => {
        const showCopy = msg.role === 'assistant' && msg.content !== '' && !msg.isError
        return (
          <Box
            key={i}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
              animation: `${fadeSlideIn} 0.3s ease`,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 0.75, px: 1 }}>
              <Avatar
                sx={
                  msg.role === 'user'
                    ? { width: 20, height: 20, ...solidAccentSx }
                    : {
                        width: 20,
                        height: 20,
                        bgcolor: theme => alpha(theme.palette.primary.main, 0.12),
                        color: 'primary.main',
                      }
                }
              >
                {msg.role === 'user' ? (
                  <Person sx={{ fontSize: 13 }} />
                ) : (
                  <SmartToy sx={{ fontSize: 13 }} />
                )}
              </Avatar>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500 }}>
                {msg.role === 'user' ? 'You' : 'Assistant'}
              </Typography>
            </Box>
            <Paper
              elevation={0}
              sx={
                msg.role === 'user'
                  ? {
                      ...solidAccentSx,
                      maxWidth: '75%',
                      px: 2,
                      py: 1.25,
                      borderRadius: '18px 18px 4px 18px',
                      boxShadow: theme => softShadow[theme.palette.mode],
                    }
                  : {
                      maxWidth: '75%',
                      px: 2,
                      py: 1.25,
                      pr: showCopy ? 4 : 2,
                      borderRadius: '18px 18px 18px 4px',
                      bgcolor: msg.isError
                        ? (theme: Theme) => alpha(theme.palette.error.main, 0.08)
                        : 'background.paper',
                      border: msg.isError ? (theme: Theme) => `1px solid ${alpha(theme.palette.error.main, 0.3)}` : 'none',
                      position: 'relative',
                      boxShadow: theme => softShadow[theme.palette.mode],
                      '&:hover .copy-button, &:focus-within .copy-button': { opacity: 1 },
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
              ) : msg.role === 'assistant' ? (
                <MarkdownContent content={msg.content} isError={msg.isError} />
              ) : (
                <Typography
                  variant="body2"
                  sx={{
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {msg.content}
                </Typography>
              )}
              {showCopy && (
                <Box
                  className="copy-button"
                  sx={{ position: 'absolute', top: 4, right: 4, opacity: 0, transition: 'opacity 0.15s ease' }}
                >
                  <CopyButton text={msg.content} />
                </Box>
              )}
            </Paper>
          </Box>
        )
      })}
      <div ref={bottomRef} />
    </Box>
  )
}
