import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import FileUpload, { UploadedFile } from './components/FileUpload'
import { useLanguage } from './i18n'

export interface ConvFile {
  id: string
  name: string
}

export interface Conversation {
  id: string
  fileIds: string[]
  files: ConvFile[]
  title: string
  updatedAt: string
}

const STORAGE_KEY = 'doc_qa_conversations'

function loadConversations(): Conversation[] {
  try {
    const raw: any[] = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return raw.map((c) => ({
      ...c,
      fileIds: c.fileIds ?? (c.fileId ? [c.fileId] : []),
      files: c.files ?? (c.fileId ? [{ id: c.fileId, name: c.filename ?? '' }] : []),
    }))
  } catch {
    return []
  }
}

function saveConversations(convs: Conversation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convs))
}

function buildTitle(files: ConvFile[], lang: string): string {
  if (!files.length) return lang === 'en' ? 'New conversation' : 'Hội thoại mới'
  if (files.length === 1) return files[0].name
  return `${files[0].name} +${files.length - 1}`
}

export default function App() {
  const { lang, t } = useLanguage()
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

  const handleUploaded = (uploaded: UploadedFile[]) => {
    const files: ConvFile[] = uploaded.map((u) => ({ id: u.fileId, name: u.filename }))
    const newConv: Conversation = {
      id: Math.random().toString(36).slice(2),
      fileIds: files.map((f) => f.id),
      files,
      title: buildTitle(files, lang),
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
            fileIds={activeConv.fileIds}
            files={activeConv.files}
            onFirstMessage={(title) => handleFirstMessage(activeConv.id, title)}
          />
        ) : (
          <div style={styles.welcome}>
            <h2 style={styles.welcomeTitle}>Doc-QA Assistant</h2>
            <p style={styles.welcomeHint}>{t('uploadHint')}</p>
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
    background: 'var(--bg-deep)',
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
    color: 'var(--text-0)',
  },
  welcomeHint: {
    fontSize: 14,
    color: 'var(--text-1)',
  },
}
