const BASE = '/api'

export type DocumentInfo = {
  filename: string
  chunks: number
}

async function parseErrorMessage(res: Response): Promise<string> {
  const text = await res.text()
  try {
    const data: unknown = JSON.parse(text)
    if (typeof data === 'object' && data !== null && 'detail' in data) {
      const { detail } = data as { detail: unknown }
      if (typeof detail === 'string') return detail
      // FastAPI's automatic validation errors shape `detail` as a list of
      // { msg, loc, type } objects rather than a single string.
      if (Array.isArray(detail)) {
        return detail
          .map(item => {
            const msg = typeof item === 'object' && item !== null && 'msg' in item ? (item as { msg: unknown }).msg : undefined
            return typeof msg === 'string' ? msg : JSON.stringify(item)
          })
          .join('; ')
      }
    }
  } catch {
    // body wasn't JSON — fall through and use the raw text
  }
  return text
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${BASE}/documents`)
  if (!res.ok) throw new Error(await parseErrorMessage(res))
  const data: { documents: DocumentInfo[] } = await res.json()
  return data.documents
}

export async function deleteDocument(filename: string): Promise<void> {
  const res = await fetch(`${BASE}/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await parseErrorMessage(res))
}

export async function uploadFile(file: File): Promise<{ filename: string; chunks_indexed: number }> {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await parseErrorMessage(res))
  return res.json()
}

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

// `history` defaults last so the existing call site in the (hand-written)
// useStream.ts keeps working until it's updated to pass conversation history.
export async function queryStream(question: string, topK: number, signal?: AbortSignal, history: ChatMessage[] = []): Promise<Response> {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK, history }),
    signal,
  })
  if (!res.ok) throw new Error(await parseErrorMessage(res))
  return res
}
