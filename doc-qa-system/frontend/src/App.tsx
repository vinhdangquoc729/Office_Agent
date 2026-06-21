import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import FileUpload from './components/FileUpload'

export interface Conversation {
  id: string
  fileId: string
  filename: string
  title: string
  updatedAt: string
}

const STORAGE_KEY = 'doc_qa_conversations'

function loadConversations(): Conversation[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function saveConversations(convs: Conversation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convs))
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(loadConversations)
  const [activeConvId, setActiveConvId] = useState<string | null>(
    () => localStorage.getItem('doc_qa_active_conv')
  )

  const activeConv = conversations.find((c) => c.id === activeConvId) ?? null

  const setActive = (id: string | null) => {
    setActiveConvId(id)
    if (id) localStorage.setItem('doc_qa_active_conv', id)
    else localStorage.removeItem('doc_qa_active_conv')
  }

  const handleUploaded = (fileId: string, filename: string) => {
    const newConv: Conversation = {
      id: Math.random().toString(36).slice(2),
      fileId,
      filename,
      title: filename,
      updatedAt: new Date().toISOString(),
    }
    const updated = [newConv, ...conversations]
    setConversations(updated)
    saveConversations(updated)
    setActive(newConv.id)
  }

  const handleFirstMessage = (convId: string, title: string) => {
    const updated = conversations.map((c) =>
      c.id === convId ? { ...c, title, updatedAt: new Date().toISOString() } : c
    )
    setConversations(updated)
    saveConversations(updated)
  }

  return (
    <div style={styles.root}>
      <Sidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelect={setActive}
        onNewChat={() => setActive(null)}
      />

      <main style={styles.main}>
        {activeConv ? (
          <ChatWindow
            key={activeConv.id}
            conversationId={activeConv.id}
            fileId={activeConv.fileId}
            filename={activeConv.filename}
            onFirstMessage={(title) => handleFirstMessage(activeConv.id, title)}
          />
        ) : (
          <div style={styles.welcome}>
            <h2 style={styles.welcomeTitle}>Doc-QA Assistant</h2>
            <p style={styles.welcomeHint}>Upload file để bắt đầu hội thoại mới</p>
            <div style={{ width: '100%', maxWidth: 480 }}>
              <FileUpload onUploaded={handleUploaded} />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    width: '100%',
    height: '100%',
    overflow: 'hidden',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    background: '#fff',
  },
  welcome: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    padding: 40,
  },
  welcomeTitle: {
    fontSize: 26,
    fontWeight: 700,
    color: '#1f2328',
  },
  welcomeHint: {
    fontSize: 14,
    color: '#888',
  },
}
