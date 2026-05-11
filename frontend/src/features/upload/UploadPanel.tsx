import { useState } from 'react'
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material'
import { CloudUpload } from '@mui/icons-material'
import { uploadFile } from '../../api/client'
import { gradientSx } from '../../theme'

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
    <Box>
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
        Documents
      </Typography>
      <Button
        component="label"
        variant="contained"
        fullWidth
        disabled={status === 'uploading'}
        startIcon={
          status === 'uploading' ? <CircularProgress size={16} color="inherit" /> : <CloudUpload />
        }
        sx={{ ...gradientSx, borderRadius: 2, textTransform: 'none', py: 1.2 }}
      >
        {status === 'uploading' ? 'Uploading…' : 'Upload PDF or TXT'}
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={handleChange}
          disabled={status === 'uploading'}
          style={{ display: 'none' }}
        />
      </Button>
      {message && (
        <Alert
          severity={status === 'done' ? 'success' : 'error'}
          sx={{ mt: 1.5, borderRadius: 2 }}
        >
          {message}
        </Alert>
      )}
    </Box>
  )
}
