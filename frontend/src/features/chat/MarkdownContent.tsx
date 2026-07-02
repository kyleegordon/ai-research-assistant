import { Box } from '@mui/material'
import { alpha, type Theme } from '@mui/material/styles'
import ReactMarkdown from 'react-markdown'

interface Props {
  content: string
  isError?: boolean
}

export default function MarkdownContent({ content, isError }: Props) {
  return (
    <Box
      sx={{
        fontSize: '0.875rem',
        lineHeight: 1.6,
        color: isError ? 'error.main' : 'text.primary',
        '& > :first-of-type': { mt: 0 },
        '& > :last-child': { mb: 0 },
        '& p': { m: 0, mb: 1 },
        '& ul, & ol': { m: 0, mb: 1, pl: 3 },
        '& li': { mb: 0.25 },
        '& h1, & h2, & h3, & h4, & h5, & h6': { mt: 1.5, mb: 0.75, fontWeight: 600, lineHeight: 1.3 },
        '& h1': { fontSize: '1.25rem' },
        '& h2': { fontSize: '1.125rem' },
        '& h3, & h4, & h5, & h6': { fontSize: '1rem' },
        '& strong': { fontWeight: 600 },
        '& blockquote': {
          m: 0,
          mb: 1,
          pl: 1.5,
          borderLeft: (theme: Theme) => `3px solid ${alpha(theme.palette.text.primary, 0.2)}`,
          color: 'text.secondary',
        },
        '& code': {
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontSize: '0.8125rem',
          bgcolor: (theme: Theme) => alpha(theme.palette.text.primary, 0.08),
          borderRadius: '4px',
          px: 0.5,
          py: 0.125,
        },
        '& pre': {
          m: 0,
          mb: 1,
          p: 1.5,
          borderRadius: '8px',
          bgcolor: (theme: Theme) => alpha(theme.palette.text.primary, 0.06),
          overflowX: 'auto',
        },
        '& pre code': { bgcolor: 'transparent', p: 0 },
        '& a': { color: 'primary.main' },
      }}
    >
      <ReactMarkdown>{content}</ReactMarkdown>
    </Box>
  )
}
