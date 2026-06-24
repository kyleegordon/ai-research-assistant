import { Box, CircularProgress, IconButton, List, ListItem, ListItemText, Tooltip, Typography } from '@mui/material'
import { DeleteOutlined } from '@mui/icons-material'
import type { DocumentInfo } from '../../api/client'

type Props = {
  documents: DocumentInfo[]
  loading: boolean
  deletingFilenames: Set<string>
  onDelete: (filename: string) => void
}

export default function DocumentList({ documents, loading, deletingFilenames, onDelete }: Props) {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
        <CircularProgress size={20} />
      </Box>
    )
  }

  if (documents.length === 0) {
    return (
      <Typography variant="body2" sx={{ color: 'text.secondary', mt: 1.5 }}>
        No documents yet.
      </Typography>
    )
  }

  return (
    <List dense disablePadding sx={{ mt: 1.5 }}>
      {documents.map(doc => (
        <ListItem
          key={doc.filename}
          disableGutters
          secondaryAction={
            <Tooltip title="Remove from knowledge base">
              <span>
                <IconButton
                  edge="end"
                  size="small"
                  onClick={() => onDelete(doc.filename)}
                  disabled={deletingFilenames.has(doc.filename)}
                >
                  {deletingFilenames.has(doc.filename) ? (
                    <CircularProgress size={16} />
                  ) : (
                    <DeleteOutlined fontSize="small" />
                  )}
                </IconButton>
              </span>
            </Tooltip>
          }
          sx={{ py: 0.5 }}
        >
          <ListItemText
            sx={{ mr: 1, overflow: 'hidden' }}
            primary={doc.filename}
            secondary={`${doc.chunks} chunk${doc.chunks === 1 ? '' : 's'}`}
            slotProps={{
              primary: { variant: 'body2', noWrap: true, title: doc.filename },
              secondary: { variant: 'caption' },
            }}
          />
        </ListItem>
      ))}
    </List>
  )
}
