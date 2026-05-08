import { useState } from 'react'
import { uploadFile } from '../../api/client'
import styles from './UploadPanel.module.css'

export default function UploadPanel() {
  const [status, setStatus] = useState<'idle' | 'uploading' | 'done' | 'error'>('idle')
  const [message, setMessage] = useState('')

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setStatus('uploading')
    setMessage('')

    try {
      const result = await uploadFile(file)
      setStatus('done')
      setMessage(`Indexed ${result.chunks_indexed} chunks from "${result.filename}"`)
    } catch (err) {
      setStatus('error')
      setMessage('Upload failed. Check that the backend is running.')
    }
  }

  return (
    <div className={styles.panel}>
      <h2 className={styles.heading}>Documents</h2>
      <label className={styles.uploadLabel}>
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={handleChange}
          disabled={status === 'uploading'}
          className={styles.input}
        />
        {status === 'uploading' ? 'Uploading…' : 'Upload PDF or TXT'}
      </label>
      {message && (
        <p className={`${styles.message} ${styles[status]}`}>{message}</p>
      )}
    </div>
  )
}
