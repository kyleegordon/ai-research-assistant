import { useEffect, useState } from 'react'
import { Alert, Box, Button, CircularProgress, Collapse, Paper, Typography } from '@mui/material'
import { CloudUpload } from '@mui/icons-material'
import { deleteDocument, listDocuments, uploadFile, type DocumentInfo } from '../../api/client'
import { gradientSx, shimmerSx, softShadow } from '../../theme'
import DocumentList from './DocumentList'

const SUCCESS_ALERT_DURATION_MS = 4000

type AlertState = { severity: 'success' | 'error'; message: string }

export default function UploadPanel() {
  const [uploading, setUploading] = useState(false)
  const [alert, setAlert] = useState<AlertState | null>(null)
  const [alertOpen, setAlertOpen] = useState(false)
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [deletingFilenames, setDeletingFilenames] = useState<Set<string>>(new Set())

  useEffect(() => {
    async function loadDocuments() {
      try {
        setDocuments(await listDocuments())
      } catch {
        // keep the empty list visible; upload/delete actions surface their own errors
      } finally {
        setLoadingDocs(false)
      }
    }
    loadDocuments()
  }, [])

  useEffect(() => {
    if (alert?.severity !== 'success') return
    const timer = setTimeout(() => setAlertOpen(false), SUCCESS_ALERT_DURATION_MS)
    return () => clearTimeout(timer)
  }, [alert])

  function showAlert(severity: AlertState['severity'], message: string) {
    setAlert({ severity, message })
    setAlertOpen(true)
  }

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setAlertOpen(false)

    try {
      const result = await uploadFile(file)
      showAlert('success', `Indexed ${result.chunks_indexed} chunks from "${result.filename}"`)
      setDocuments(prev => {
        const next = { filename: result.filename, chunks: result.chunks_indexed }
        const idx = prev.findIndex(doc => doc.filename === result.filename)
        return idx === -1 ? [...prev, next] : prev.map((doc, i) => (i === idx ? next : doc))
      })
    } catch (err) {
      showAlert('error', err instanceof Error ? err.message : 'Upload failed. Check that the backend is running.')
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(filename: string) {
    setDeletingFilenames(prev => new Set(prev).add(filename))
    setAlertOpen(false)
    try {
      await deleteDocument(filename)
      setDocuments(prev => prev.filter(doc => doc.filename !== filename))
    } catch (err) {
      showAlert('error', err instanceof Error ? err.message : `Failed to remove "${filename}".`)
    } finally {
      setDeletingFilenames(prev => {
        const next = new Set(prev)
        next.delete(filename)
        return next
      })
    }
  }

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        borderRadius: 3,
        boxShadow: theme => softShadow[theme.palette.mode],
      }}
    >
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
        Documents
      </Typography>
      <Button
        component="label"
        variant="contained"
        fullWidth
        disabled={uploading}
        startIcon={uploading ? <CircularProgress size={16} color="inherit" /> : <CloudUpload />}
        sx={{ ...gradientSx, ...shimmerSx, borderRadius: 2, py: 1.2 }}
      >
        {uploading ? 'Uploading…' : 'Upload PDF'}
        <Box
          component="input"
          type="file"
          accept=".pdf"
          onChange={handleChange}
          disabled={uploading}
          sx={{ display: 'none' }}
        />
      </Button>
      <Collapse in={alertOpen} onExited={() => setAlert(null)}>
        {alert && (
          <Alert severity={alert.severity} sx={{ mt: 1.5, borderRadius: 2 }}>
            {alert.message}
          </Alert>
        )}
      </Collapse>
      <DocumentList
        documents={documents}
        loading={loadingDocs}
        deletingFilenames={deletingFilenames}
        onDelete={handleDelete}
      />
    </Paper>
  )
}
