// Write this yourself — core RAG component (SSE streaming hook)
import { useState } from 'react'

export function useStream() {
  const [streaming, setStreaming] = useState(false)

  /**
   * Implement this:
   * 1. POST to /api/query with { question }
   * 2. Read the response body as a ReadableStream
   * 3. Decode each SSE chunk ("data: <token>\n\n") and call onToken(token)
   * 4. Stop when you receive "data: [DONE]" or the stream closes
   * 5. Set streaming true/false around the operation
   */
  async function stream(question: string, onToken: (token: string) => void) {
    throw new Error('Not implemented')
  }

  return { stream, streaming }
}
