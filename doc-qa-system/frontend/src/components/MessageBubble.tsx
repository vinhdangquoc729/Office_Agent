import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import DownloadButton from './DownloadButton'
import { OutputFile } from '../api/client'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  output_files?: OutputFile[]
}

const mdComponents = {
  p: ({ children }: any) => <p style={{ margin: '0 0 8px' }}>{children}</p>,
  ul: ({ children }: any) => <ul style={{ paddingLeft: 20, margin: '4px 0 8px' }}>{children}</ul>,
  ol: ({ children }: any) => <ol style={{ paddingLeft: 20, margin: '4px 0 8px' }}>{children}</ol>,
  li: ({ children }: any) => <li style={{ marginBottom: 2 }}>{children}</li>,
  hr: () => <hr style={{ border: 'none', borderTop: '1px solid #e8eaed', margin: '10px 0' }} />,
  em: ({ children }: any) => <em style={{ color: '#666', fontSize: 12 }}>{children}</em>,
  strong: ({ children }: any) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
  code: ({ children }: any) => <code style={{ background: '#f0f0f0', padding: '1px 5px', borderRadius: 4, fontSize: 13 }}>{children}</code>,
  table: ({ children }: any) => (
    <div style={{ overflowX: 'auto', margin: '8px 0' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}>{children}</table>
    </div>
  ),
  th: ({ children }: any) => (
    <th style={{ border: '1px solid #d0d7de', padding: '6px 10px', background: '#f6f8fa', fontWeight: 600, textAlign: 'left' }}>{children}</th>
  ),
  td: ({ children }: any) => (
    <td style={{ border: '1px solid #d0d7de', padding: '6px 10px' }}>{children}</td>
  ),
}

export default function MessageBubble({ role, content, output_files = [] }: Message) {
  const isUser = role === 'user'
  return (
    <div style={{ ...styles.row, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      {!isUser && <div style={styles.avatar}>🤖</div>}
      <div style={{ ...styles.bubble, ...(isUser ? styles.userBubble : styles.assistantBubble) }}>
        {isUser ? (
          <span>{content}</span>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{content}</ReactMarkdown>
        )}
        <DownloadButton files={output_files} />
      </div>
      {isUser && <div style={styles.avatar}>👤</div>}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  row: { display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 12 },
  avatar: { fontSize: 22, flexShrink: 0 },
  bubble: {
    maxWidth: '70%',
    padding: '10px 14px',
    borderRadius: 12,
    fontSize: 14,
    lineHeight: 1.6,
    wordBreak: 'break-word',
  },
  userBubble: { background: '#0969da', color: '#fff', borderBottomRightRadius: 3 },
  assistantBubble: { background: '#fff', color: '#1f2328', borderBottomLeftRadius: 3, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
}
