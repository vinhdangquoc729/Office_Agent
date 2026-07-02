import { useEffect, useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import { sendMessageStream } from '../api/client'
import MessageBubble, { Message } from './MessageBubble'
import { ConvFile } from '../App'

interface Props {
  conversationId: string
  fileIds: string[]
  files: ConvFile[]
  onFirstMessage: (title: string) => void
}

const msgKey = (id: string) => `doc_qa_msgs_${id}`

function buildWelcome(files: ConvFile[]): string {
  if (!files.length) return 'Bạn muốn hỏi gì?'
  const names = files.map((f) => `**${f.name}**`).join(', ')
  return `Đã tải ${names}. Bạn muốn hỏi gì về tài liệu này?`
}

function loadMessages(conversationId: string, files: ConvFile[]): Message[] {
  try {
    const saved = localStorage.getItem(msgKey(conversationId))
    if (saved) return JSON.parse(saved)
  } catch { /* ignore */ }
  return [{ role: 'assistant', content: buildWelcome(files) }]
}

function saveMessages(conversationId: string, messages: Message[]) {
  try {
    localStorage.setItem(msgKey(conversationId), JSON.stringify(messages))
  } catch { /* ignore */ }
}

export default function ChatWindow({ conversationId, fileIds, files, onFirstMessage }: Props) {
  const [messages, setMessages] = useState<Message[]>(() => loadMessages(conversationId, files))
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const firstMessageSent = useRef(messages.some((m) => m.role === 'user'))

  useEffect(() => {
    const msgs = loadMessages(conversationId, files)
    setMessages(msgs)
    firstMessageSent.current = msgs.some((m) => m.role === 'user')
  }, [conversationId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return

    const newMessages: Message[] = [...messages, { role: 'user', content: text }]
    setInput('')
    setLoading(true)
    saveMessages(conversationId, newMessages)

    if (!firstMessageSent.current) {
      firstMessageSent.current = true
      onFirstMessage(text.length > 55 ? text.slice(0, 55) + '…' : text)
    }

    const placeholder: Message = { role: 'assistant', content: '', activity: 'Đang kết nối...' }
    setMessages([...newMessages, placeholder])

    try {
      for await (const event of sendMessageStream(fileIds, files.map((f) => f.name), text, conversationId)) {
        if (event.type === 'activity') {
          flushSync(() => {
            setMessages((prev) => {
              const last = { ...prev[prev.length - 1], activity: event.text }
              return [...prev.slice(0, -1), last]
            })
          })
        } else if (event.type === 'token') {
          setMessages((prev) => {
            const last = { ...prev[prev.length - 1], content: prev[prev.length - 1].content + (event.text ?? '') }
            return [...prev.slice(0, -1), last]
          })
        } else if (event.type === 'done') {
          setMessages((prev) => {
            const cur = prev[prev.length - 1]
            const finalMsg: Message = {
              ...cur,
              activity: '',
              output_files: event.output_files ?? [],
              content: event.content || cur.content || 'Xử lý hoàn tất.',
            }
            const final = [...prev.slice(0, -1), finalMsg]
            saveMessages(conversationId, final)
            return final
          })
        } else if (event.type === 'error') {
          setMessages((prev) => {
            const last = { ...prev[prev.length - 1], activity: '', content: `Lỗi: ${event.text}` }
            const final = [...prev.slice(0, -1), last]
            saveMessages(conversationId, final)
            return final
          })
        }
      }
    } catch {
      setMessages((prev) => {
        const last = { ...prev[prev.length - 1], activity: '', content: 'Lỗi kết nối tới server.' }
        const final = [...prev.slice(0, -1), last]
        saveMessages(conversationId, final)
        return final
      })
    } finally {
      setLoading(false)
    }
  }

  const headerLabel = files.length === 1
    ? files[0].name
    : `${files[0]?.name ?? ''} +${files.length - 1} file`

  const downloadLinks = files.map((f) => {
    const ext = f.name.slice(f.name.lastIndexOf('.'))
    return { name: f.name, url: `/download/${f.id}${ext}` }
  })

  return (
    <div style={styles.container}>
      <div style={styles.chatHeader}>
        <span style={styles.fileIcon}>📎</span>
        <span style={styles.fileName} title={files.map((f) => f.name).join(', ')}>{headerLabel}</span>
        <div style={styles.downloadGroup}>
          {downloadLinks.map((d) => (
            <a
              key={d.url}
              href={d.url}
              download={d.name}
              style={styles.downloadBtn}
              title={`Tải xuống ${d.name}`}
            >
              {files.length > 1 ? d.name : 'Tải xuống'}
            </a>
          ))}
        </div>
      </div>

      <div style={styles.messages}>
        {messages.map((m, i) => <MessageBubble key={i} {...m} />)}
        <div ref={bottomRef} />
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Nhập yêu cầu... (Enter để gửi)"
          disabled={loading}
        />
        <button style={styles.btn} onClick={send} disabled={loading || !input.trim()}>
          Gửi
        </button>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    overflow: 'hidden',
  },
  chatHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '12px 16px',
    borderBottom: '1px solid #e8eaed',
    background: '#fff',
    flexShrink: 0,
  },
  fileIcon: { fontSize: 16 },
  fileName: { fontSize: 13, fontWeight: 600, color: '#1f2328', flex: 1 },
  downloadGroup: { display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 },
  downloadBtn: {
    fontSize: 12,
    color: '#0969da',
    textDecoration: 'none',
    padding: '3px 10px',
    border: '1px solid #0969da',
    borderRadius: 6,
    fontWeight: 500,
    whiteSpace: 'nowrap' as const,
    maxWidth: 140,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    display: 'inline-block',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px 12px',
    background: '#f6f8fa',
  },
  inputRow: {
    display: 'flex',
    gap: 8,
    padding: '10px 12px',
    borderTop: '1px solid #e8eaed',
    background: '#fff',
    flexShrink: 0,
  },
  input: {
    flex: 1,
    padding: '9px 14px',
    border: '1px solid #d0d7de',
    borderRadius: 8,
    fontSize: 14,
    outline: 'none',
    background: '#fff',
  },
  btn: {
    padding: '9px 20px',
    background: '#0969da',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  },
}
