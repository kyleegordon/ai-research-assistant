const BASE = '/api'

export async function uploadFile(file: File): Promise<{ filename: string; chunks_indexed: number }> {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function queryStream(question: string, topK = 5): Promise<Response> {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res
}
