import { useState } from 'react'
import { Box, Button, TextField } from '@mui/material'
import { Send, Stop } from '@mui/icons-material'
import { glassSx, gradientSx, shimmerSx } from '../../theme'

type Props = {
  onSubmit: (question: string) => void
  disabled: boolean
  streaming: boolean
  stop: () => void
}

export default function MessageInput({ onSubmit, disabled, streaming, stop }: Props) {
  const [value, setValue] = useState('')

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    submit()
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        display: 'flex',
        gap: 1,
        p: 2,
        ...glassSx('0 -1px 0'),
      }}
    >
      <TextField
        fullWidth
        size="small"
        multiline
        maxRows={6}
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about your documents…"
        disabled={disabled}
        variant="outlined"
      />
      {streaming ? (
        <Button
          type="button"
          variant="contained"
          onClick={stop}
          endIcon={<Stop />}
          sx={{ ...gradientSx, ...shimmerSx, borderRadius: 2, px: 2.5, whiteSpace: 'nowrap' }}
        >
          Stop
        </Button>
      ) : (
        <Button
          type="submit"
          variant="contained"
          disabled={disabled || !value.trim()}
          endIcon={<Send />}
          sx={{ ...gradientSx, ...shimmerSx, borderRadius: 2, px: 2.5, whiteSpace: 'nowrap' }}
        >
          Send
        </Button>
      )}
    </Box>
  )
}
