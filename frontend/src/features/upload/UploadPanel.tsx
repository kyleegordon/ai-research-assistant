import { useEffect, useState, type DragEvent } from 'react'
import { Alert, Box, Button, CircularProgress, Collapse, Paper, Tooltip, Typography } from '@mui/material'
import { CloudUpload } from '@mui/icons-material'
import { deleteDocument, listDocuments, uploadFile, type DocumentInfo } from '../../api/client'
import { gradientSx, shimmerSx, softShadow } from '../../theme'
import DocumentList from './DocumentList'

const SUCCESS_ALERT_DURATION_MS = 4000

type AlertState = { severity: 'success' | 'error'; message: string }

type UploadOutcome = { filename: string; chunksIndexed: number }

export default function UploadPanel() {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{ current: number; total: number } | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
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

  // Uploads a single file and applies its result to the document list.
  // Returns the outcome on success, or null if the upload failed (the
  // error is swallowed here so callers can keep processing the rest of
  // a batch and report failures in one combined summary).
  async function uploadOne(file: File): Promise<UploadOutcome | null> {
    try {
      const result = await uploadFile(file)
      setDocuments(prev => {
        const next = { filename: result.filename, chunks: result.chunks_indexed }
        const idx = prev.findIndex(doc => doc.filename === result.filename)
        return idx === -1 ? [...prev, next] : prev.map((doc, i) => (i === idx ? next : doc))
      })
      return { filename: result.filename, chunksIndexed: result.chunks_indexed }
    } catch {
      return null
    }
  }

  // Uploads files one at a time (sequential, not concurrent) and rolls
  // the results up into a single summary alert.
  async function uploadFiles(files: File[]) {
    if (files.length === 0) return

    setUploading(true)
    setAlertOpen(false)

    const succeeded: UploadOutcome[] = []
    let failedCount = 0

    for (let i = 0; i < files.length; i++) {
      setUploadProgress({ current: i + 1, total: files.length })
      const outcome = await uploadOne(files[i])
      if (outcome) {
        succeeded.push(outcome)
      } else {
        failedCount += 1
      }
    }

    setUploading(false)
    setUploadProgress(null)

    if (files.length === 1) {
      if (succeeded.length === 1) {
        showAlert('success', `Indexed ${succeeded[0].chunksIndexed} chunks from "${succeeded[0].filename}"`)
      } else {
        showAlert('error', 'Upload failed. Check that the backend is running.')
      }
      return
    }

    if (succeeded.length === 0) {
      showAlert('error', `Upload failed for all ${files.length} files. Check that the backend is running.`)
      return
    }

    const totalChunks = succeeded.reduce((sum, doc) => sum + doc.chunksIndexed, 0)
    const failureSuffix = failedCount > 0 ? ` (${failedCount} failed)` : ''
    showAlert(
      failedCount > 0 ? 'error' : 'success',
      `Indexed ${succeeded.length} file${succeeded.length === 1 ? '' : 's'} (${totalChunks} chunks)${failureSuffix}`,
    )
  }

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    e.target.value = ''
    await uploadFiles(files)
  }

  function handleDragOver(e: DragEvent<HTMLElement>) {
    e.preventDefault()
    if (uploading) return
    setIsDragOver(true)
  }

  function handleDragLeave(e: DragEvent<HTMLElement>) {
    e.preventDefault()
    setIsDragOver(false)
  }

  async function handleDrop(e: DragEvent<HTMLElement>) {
    e.preventDefault()
    setIsDragOver(false)
    if (uploading) return

    const files = Array.from(e.dataTransfer.files).filter(file => file.name.toLowerCase().endsWith('.pdf') || file.name.toLowerCase().endsWith('.txt'))
    await uploadFiles(files)
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
      <Box
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{
          borderRadius: 2,
          transition: 'box-shadow 0.15s ease, transform 0.15s ease',
          ...(isDragOver && {
            boxShadow: theme => `0 0 0 2px ${theme.palette.primary.main}`,
            transform: 'scale(1.01)',
          }),
        }}
      >
        <Tooltip title="Accepts .pdf and .txt files" placement="top">
          <span style={{ display: 'block' }}>
            <Button
              component="label"
              variant="contained"
              fullWidth
              disabled={uploading}
              startIcon={uploading ? <CircularProgress size={16} color="inherit" /> : <CloudUpload />}
              sx={{ ...gradientSx, ...shimmerSx, borderRadius: 2, py: 1.2 }}
            >
              {uploading
                ? uploadProgress && uploadProgress.total > 1
                  ? `Uploading ${uploadProgress.current} of ${uploadProgress.total}…`
                  : 'Uploading…'
                : isDragOver
                  ? 'Drop to upload'
                  : 'Upload'}
              <Box
                component="input"
                type="file"
                accept=".pdf,.txt"
                multiple
                onChange={handleChange}
                disabled={uploading}
                sx={{ display: 'none' }}
              />
            </Button>
          </span>
        </Tooltip>
      </Box>
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
