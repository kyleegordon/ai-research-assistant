import type { Message } from './ChatWindow'
import styles from './MessageList.module.css'

export default function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div className={styles.list}>
      {messages.length === 0 && (
        <p className={styles.empty}>Upload a document and ask a question.</p>
      )}
      {messages.map((msg, i) => (
        <div key={i} className={`${styles.message} ${styles[msg.role]}`}>
          <span className={styles.role}>{msg.role === 'user' ? 'You' : 'Assistant'}</span>
          <p>{msg.content || '…'}</p>
        </div>
      ))}
    </div>
  )
}
