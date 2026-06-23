// Write this yourself — core RAG component (SSE streaming hook)
import { useState } from 'react'

/**
 * 1. POSTs the question to /api/query and reads the response as a stream
 * 2. Decodes each SSE chunk and calls onToken with the extracted text
 * 3. Stops when [DONE] is received or the stream closes
 * 4. Tracks streaming state via the returned `streaming` boolean
 */

export function useStream() {
  const [streaming, setStreaming] = useState(false)

  async function stream(question: string, onToken: (token: string) => void) {
    setStreaming(true)
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) throw new Error(`Query failed: ${response.status}`)

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop()!

        for (const part of parts) {
          const token = part.replace(/^data:[ ]?/, '')
          const trimmed = token.trim()
          if (!trimmed) continue
          if (trimmed === '[DONE]') return
          onToken(token)
        }
      }
    } finally {
      setStreaming(false)
    }
  }

  return { stream, streaming }
}
