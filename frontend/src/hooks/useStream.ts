// Write this yourself — core RAG component (SSE streaming hook)
import { useRef, useState } from 'react'
import { queryStream } from '../api/client'

/**
 * 1. POSTs the question to /api/query (via queryStream) and reads the response as a stream
 * 2. Decodes each SSE chunk and calls onToken with the extracted text
 * 3. Stops when [DONE] is received or the stream closes
 * 4. Tracks streaming state via the returned `streaming` boolean
 * 5. `stop()` aborts the in-flight request via AbortController
 */

export function useStream() {
  const [streaming, setStreaming] = useState(false)

  const abortControllerRef = useRef<AbortController | null>(null)

  async function stream(question: string, onToken: (token: string) => void, onError: (message: string) => void, topK = 5) {
    const controller = new AbortController()
    abortControllerRef.current = controller
    setStreaming(true)
    try {
      const response = await queryStream(question, topK, controller.signal)
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
          const lines = part.split('\n')
          const isError = lines.some(line => line === 'event: error')

          if (isError) {
            const dataLine = lines.find(line => line.startsWith('data:'))
            const message = dataLine?.replace(/^data:[ ]?/, '') ?? 'Unknown error'
            onError(message)
            reader.cancel()
            return
          }

          const token = part.replace(/^data:[ ]?/, '')
          const trimmed = token.trim()
          if (!trimmed) continue
          if (trimmed === '[DONE]') return
          onToken(token)
        }
      }
    } finally {
      setStreaming(false)
      abortControllerRef.current = null
    }
  }

  function stop() {
    abortControllerRef.current?.abort()
  }

  return { stream, streaming, stop }
}
