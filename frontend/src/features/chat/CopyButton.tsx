import { useState } from 'react'
import { IconButton, Tooltip } from '@mui/material'
import { ContentCopy } from '@mui/icons-material'

type Props = {
  text: string
}

export default function CopyButton({ text }: Props) {
  const [copied, setCopied] = useState(false)

  async function handleClick() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Tooltip title={copied ? 'Copied!' : 'Copy'}>
      <IconButton
        size="small"
        onClick={handleClick}
        sx={{ color: 'text.secondary' }}
        aria-label="Copy response to clipboard"
      >
        <ContentCopy sx={{ fontSize: 16 }} />
      </IconButton>
    </Tooltip>
  )
}
