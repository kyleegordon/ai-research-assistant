import { useState } from 'react'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { useStream } from '../../hooks/useStream'
import styles from './ChatWindow.module.css'

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
    <div className={styles.window}>
      <MessageList messages={messages} />
      <MessageInput onSubmit={handleSubmit} disabled={streaming} />
    </div>
  )
}
