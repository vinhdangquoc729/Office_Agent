import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import DownloadButton from './DownloadButton'
import { OutputFile, getDownloadUrl } from '../api/client'
import { useLanguage } from '../i18n'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  output_files?: OutputFile[]
  activity?: string
}

const mdComponents = {
  p: ({ children }: any) => <p style={{ margin: '0 0 8px' }}>{children}</p>,
  ul: ({ children }: any) => <ul style={{ paddingLeft: 20, margin: '4px 0 8px' }}>{children}</ul>,
  ol: ({ children }: any) => <ol style={{ paddingLeft: 20, margin: '4px 0 8px' }}>{children}</ol>,
  li: ({ children }: any) => <li style={{ marginBottom: 2 }}>{children}</li>,
  hr: () => <hr style={{ border: 'none', borderTop: '1px solid #2e2e2e', margin: '10px 0' }} />,
  em: ({ children }: any) => <em style={{ color: '#888', fontSize: 12 }}>{children}</em>,
  strong: ({ children }: any) => <strong style={{ fontWeight: 600, color: '#f0f0f0' }}>{children}</strong>,
  code: ({ children }: any) => <code style={{ background: '#252525', color: '#b8c8f5', padding: '1px 6px', borderRadius: 4, fontSize: 12.5, fontFamily: 'ui-monospace, monospace' }}>{children}</code>,
  table: ({ children }: any) => (
    <div style={{ overflowX: 'auto', margin: '8px 0' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}>{children}</table>
    </div>
  ),
  th: ({ children }: any) => (
    <th style={{ border: '1px solid #2e2e2e', padding: '6px 10px', background: '#1e1e1e', fontWeight: 600, textAlign: 'left', color: '#d0d0d0' }}>{children}</th>
  ),
  td: ({ children }: any) => (
    <td style={{ border: '1px solid #2a2a2a', padding: '6px 10px', color: '#c8c8c8' }}>{children}</td>
  ),
}

function ChartPreviews({ files }: { files: OutputFile[] }) {
  const { t } = useLanguage()
  const charts = files.filter((f) => f.type === 'chart')
  if (!charts.length) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 10 }}>
      {charts.map((f) => (
        <div key={f.id}>
          <img
            src={getDownloadUrl(f.id)}
            alt={f.name}
            style={{ maxWidth: '100%', borderRadius: 6, border: '1px solid #2e2e2e', display: 'block' }}
          />
          <a
            href={getDownloadUrl(f.id)}
            download={f.name}
            style={{ fontSize: 12, color: '#5c9af7', textDecoration: 'none', marginTop: 4, display: 'inline-block' }}
          >
            {t('downloadImage')}
          </a>
        </div>
      ))}
    </div>
  )
}

export default function MessageBubble({ role, content, output_files = [], activity }: Message) {
  const isUser = role === 'user'
  const docFiles = output_files.filter((f) => f.type !== 'chart')
  return (
    <div style={{ ...styles.row, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      {!isUser && <div style={styles.avatar}>🤖</div>}
      <div style={{ ...styles.bubble, ...(isUser ? styles.userBubble : styles.assistantBubble) }}>
        {isUser ? (
          <span>{content}</span>
        ) : content ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{content}</ReactMarkdown>
        ) : null}
        {!isUser && activity && <div style={styles.activity}>{activity}</div>}
        <ChartPreviews files={output_files} />
        <DownloadButton files={docFiles} />
      </div>
      {isUser && <div style={styles.avatar}>👤</div>}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  row: { display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 14 },
  avatar: { fontSize: 20, flexShrink: 0, opacity: 0.7 },
  bubble: {
    maxWidth: '72%',
    padding: '10px 14px',
    borderRadius: 12,
    fontSize: 14,
    lineHeight: 1.65,
    wordBreak: 'break-word',
  },
  userBubble: {
    background: '#4f82f7',
    color: '#fff',
    borderBottomRightRadius: 3,
  },
  assistantBubble: {
    background: '#1a1a1a',
    color: '#e0e0e0',
    borderBottomLeftRadius: 3,
    border: '1px solid #272727',
  },
  activity: {
    fontSize: 12,
    color: '#555',
    fontStyle: 'italic',
    marginTop: 6,
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
}
