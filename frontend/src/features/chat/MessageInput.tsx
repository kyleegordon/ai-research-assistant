import { useState } from 'react'
import styles from './MessageInput.module.css'

type Props = {
  onSubmit: (question: string) => void
  disabled: boolean
}

export default function MessageInput({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <input
        className={styles.input}
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder="Ask a question about your documents…"
        disabled={disabled}
      />
      <button className={styles.button} type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  )
}
