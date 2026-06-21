import { useEffect, useRef, useState } from 'react'
import { sendMessage } from '../api/client'
import MessageBubble, { Message } from './MessageBubble'

interface Props {
  conversationId: string
  fileId: string
  filename: string
  onFirstMessage: (title: string) => void
}

const msgKey = (id: string) => `doc_qa_msgs_${id}`

function loadMessages(conversationId: string, filename: string): Message[] {
  try {
    const saved = localStorage.getItem(msgKey(conversationId))
    if (saved) return JSON.parse(saved)
  } catch { /* ignore */ }
  return [{ role: 'assistant', content: `Đã tải **${filename}**. Bạn muốn hỏi gì về tài liệu này?` }]
}

function saveMessages(conversationId: string, messages: Message[]) {
  try {
    localStorage.setItem(msgKey(conversationId), JSON.stringify(messages))
  } catch { /* ignore */ }
}

export default function ChatWindow({ conversationId, fileId, filename, onFirstMessage }: Props) {
  const [messages, setMessages] = useState<Message[]>(() => loadMessages(conversationId, filename))
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const firstMessageSent = useRef(messages.some((m) => m.role === 'user'))

  // Khi đổi conversation: load messages của conversation đó từ localStorage
  useEffect(() => {
    const msgs = loadMessages(conversationId, filename)
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
    setMessages(newMessages)
    saveMessages(conversationId, newMessages)
    setLoading(true)

    if (!firstMessageSent.current) {
      firstMessageSent.current = true
      onFirstMessage(text.length > 55 ? text.slice(0, 55) + '…' : text)
    }

    try {
      const res = await sendMessage(fileId, text, conversationId)
      const reply: Message = {
        role: 'assistant',
        content: res.reply || 'Xử lý hoàn tất.',
        output_files: res.output_files,
      }
      const finalMessages = [...newMessages, reply]
      setMessages(finalMessages)
      saveMessages(conversationId, finalMessages)
    } catch {
      const errMsg: Message[] = [...newMessages, { role: 'assistant', content: 'Lỗi kết nối tới server.' }]
      setMessages(errMsg)
      saveMessages(conversationId, errMsg)
    } finally {
      setLoading(false)
    }
  }

  const ext = filename.slice(filename.lastIndexOf('.'))
  const downloadUrl = `/download/${fileId}${ext}`

  return (
    <div style={styles.container}>
      <div style={styles.chatHeader}>
        <span style={styles.fileIcon}>📎</span>
        <span style={styles.fileName}>{filename}</span>
        <a href={downloadUrl} download={filename} style={styles.downloadBtn} title="Tải xuống tài liệu gốc">
          Tải xuống
        </a>
      </div>

      <div style={styles.messages}>
        {messages.map((m, i) => <MessageBubble key={i} {...m} />)}
        {loading && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', marginBottom: 12 }}>
            <div style={{ fontSize: 22 }}>🤖</div>
            <div style={styles.typing}>Đang xử lý...</div>
          </div>
        )}
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
  downloadBtn: {
    fontSize: 12,
    color: '#0969da',
    textDecoration: 'none',
    padding: '3px 10px',
    border: '1px solid #d0d7de',
    borderRadius: 6,
    whiteSpace: 'nowrap' as const,
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px 12px',
    background: '#f6f8fa',
  },
  typing: {
    background: '#fff',
    padding: '10px 14px',
    borderRadius: 12,
    borderBottomLeftRadius: 3,
    fontSize: 14,
    color: '#666',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
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
