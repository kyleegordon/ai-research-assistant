import { useState } from 'react'
import { Box } from '@mui/material'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { useStream } from '../../hooks/useStream'

export type Message = {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([])
  const { stream, streaming } = useStream()

  async function handleSubmit(question: string) {
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    await stream(question, (token) => {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: updated[updated.length - 1].content + token,
        }
        return updated
      })
    })
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
      <MessageList messages={messages} />
      <MessageInput onSubmit={handleSubmit} disabled={streaming} />
    </Box>
  )
}
