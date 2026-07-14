import { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { useStream } from '../../hooks/useStream'
import type { ChatMessage } from '../../api/client'

export type Message = ChatMessage & {
  isError?: boolean
}

const HISTORY_KEY = 'ai-research-assistant:chat-history'

function loadHistory(): Message[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
  } catch {
    return []
  }
}

interface Props {
  clearChatRef: React.MutableRefObject<() => void>
}

export default function ChatWindow({ clearChatRef }: Props) {
  const [messages, setMessages] = useState<Message[]>(loadHistory)
  const { stream, streaming, stop } = useStream()

  useEffect(() => {
    // Don't persist a trailing assistant placeholder that's still streaming —
    // an empty, non-error message in progress would resurrect a permanently
    // stuck loading bubble on reload.
    const persistable = messages.filter(msg => msg.content !== '' || msg.isError)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(persistable))
  }, [messages])

  function handleClear() {
    setMessages([])
    localStorage.removeItem(HISTORY_KEY)
  }
  clearChatRef.current = handleClear

  async function handleSubmit(question: string) {
    // Snapshot prior turns before appending this one. Every submit appends a
    // user+assistant pair together, so `messages` is always [user, assistant,
    // user, assistant, ...] — walk it in pairs and drop the whole exchange
    // (not just the assistant half) when the reply errored or never streamed
    // any content. Dropping only the assistant half would leave an orphaned
    // user turn, breaking the strict user/assistant alternation that
    // build_retrieval_query and the chat() messages list both rely on.
    const history: ChatMessage[] = []
    for (let i = 0; i + 1 < messages.length; i += 2) {
      const userMsg = messages[i]
      const assistantMsg = messages[i + 1]
      if (assistantMsg.content !== '' && !assistantMsg.isError) {
        history.push({ role: userMsg.role, content: userMsg.content })
        history.push({ role: assistantMsg.role, content: assistantMsg.content })
      }
    }

    setMessages(prev => [...prev, { role: 'user', content: question }])
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      await stream(question, (token) => {
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            role: 'assistant',
            content: updated[updated.length - 1].content + token,
          }
          return updated
        })
      }, (errorMessage) => {
        setMessages(prev => {
          const updated = [...prev]
          const existing = updated[updated.length - 1].content
          updated[updated.length - 1] = {
            role: 'assistant',
            content: existing ? `${existing}\n\n${errorMessage}` : errorMessage,
            isError: true,
          }
          return updated
        })
      }, undefined, history)
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        // User clicked Stop — keep whatever partial text already streamed in.
        return
      }
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Something went wrong — check that the backend and Ollama are running.',
          isError: true,
        }
        return updated
      })
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
      <MessageList messages={messages} />
      <MessageInput onSubmit={handleSubmit} disabled={streaming} streaming={streaming} stop={stop} />
    </Box>
  )
}
