import { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { useStream } from '../../hooks/useStream'
import type { ChatMessage } from '../../api/client'

export type Message = ChatMessage & {
  isError?: boolean
  // Set when generation was stopped before completing — via Stop, or
  // interrupted before any token arrived. Content may be empty (stopped
  // immediately) or a partial fragment (stopped mid-stream); either way it's
  // not a finished answer, so it must never be fed back as history, and
  // persistence must keep it paired with its question (see isUsableAsHistory).
  isIncomplete?: boolean
}

// A message is only ever left blank with none of these flags set if the tab
// closed mid-stream before any callback could run — every other path (finished,
// errored, or explicitly Stopped) sets isError/isIncomplete even when content
// stays empty. Safe to drop: it never became a real exchange, and dropping it
// doesn't orphan its paired question because isIncomplete now covers Stop.
function isAbandonedPlaceholder(msg: Message): boolean {
  return msg.content === '' && !msg.isError && !msg.isIncomplete
}

// Whether a completed exchange is valid to feed back as conversation history.
// Errors and Stop-interrupted replies are real UI state (kept in `messages`
// and persisted) but must never be sent to the model as if they were finished
// answers.
function isUsableAsHistory(assistantMsg: Message): boolean {
  return assistantMsg.content !== '' && !assistantMsg.isError && !assistantMsg.isIncomplete
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
    const persistable = messages.filter(msg => !isAbandonedPlaceholder(msg))
    localStorage.setItem(HISTORY_KEY, JSON.stringify(persistable))
  }, [messages])

  function handleClear() {
    setMessages([])
    localStorage.removeItem(HISTORY_KEY)
  }
  clearChatRef.current = handleClear

  async function handleSubmit(question: string) {
    // Snapshot prior turns before appending this one. Every submit appends a
    // user+assistant pair together, and persistence now keeps both halves of
    // a pair or neither (see isAbandonedPlaceholder), so `messages` is always
    // [user, assistant, user, assistant, ...] — walk it in pairs and drop the
    // whole exchange (not just the assistant half) when it isn't usable as
    // history. Dropping only the assistant half would leave an orphaned user
    // turn, breaking the strict user/assistant alternation that
    // build_retrieval_query and the chat() messages list both rely on.
    const history: ChatMessage[] = []
    for (let i = 0; i + 1 < messages.length; i += 2) {
      const userMsg = messages[i]
      const assistantMsg = messages[i + 1]
      if (isUsableAsHistory(assistantMsg)) {
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
        // User clicked Stop — keep whatever partial text already streamed in
        // (possibly none), but mark it incomplete so it's never mistaken for
        // a finished answer downstream.
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            isIncomplete: true,
          }
          return updated
        })
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
