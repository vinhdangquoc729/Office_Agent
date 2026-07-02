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
  hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '10px 0' }} />,
  em: ({ children }: any) => <em style={{ color: 'var(--text-1)', fontSize: 12 }}>{children}</em>,
  strong: ({ children }: any) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
  code: ({ children }: any) => <code style={{ background: 'var(--code-bg)', color: 'var(--code-text)', padding: '1px 6px', borderRadius: 4, fontSize: 12.5, fontFamily: 'ui-monospace, monospace' }}>{children}</code>,
  table: ({ children }: any) => (
    <div style={{ overflowX: 'auto', margin: '8px 0' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}>{children}</table>
    </div>
  ),
  th: ({ children }: any) => (
    <th style={{ border: '1px solid var(--border)', padding: '6px 10px', background: 'var(--bg-elevated)', fontWeight: 600, textAlign: 'left', color: 'var(--text-0)' }}>{children}</th>
  ),
  td: ({ children }: any) => (
    <td style={{ border: '1px solid var(--border)', padding: '6px 10px', color: 'var(--text-1)' }}>{children}</td>
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
            style={{ maxWidth: '100%', borderRadius: 6, border: '1px solid var(--border)', display: 'block' }}
          />
          <a
            href={getDownloadUrl(f.id)}
            download={f.name}
            style={{ fontSize: 12, color: 'var(--accent-text)', textDecoration: 'none', marginTop: 4, display: 'inline-block' }}
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
    background: 'var(--bubble-u-bg)',
    color: 'var(--bubble-u-text)',
    borderBottomRightRadius: 3,
  },
  assistantBubble: {
    background: 'var(--bubble-ai-bg)',
    color: 'var(--bubble-ai-text)',
    borderBottomLeftRadius: 3,
    border: '1px solid var(--bubble-ai-bd)',
  },
  activity: {
    fontSize: 12,
    color: 'var(--text-2)',
    fontStyle: 'italic',
    marginTop: 6,
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
}
