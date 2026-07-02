import axios from 'axios'

const api = axios.create({ baseURL: '/' })

export interface OutputFile {
  id: string
  name: string
  type: 'report' | 'slide' | 'chart'
}

export interface ChatResponse {
  reply: string
  output_files: OutputFile[]
  error: string
}

export async function uploadFile(file: File): Promise<{ file_id: string; filename: string }> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload', form)
  return data
}

export async function sendMessage(
  fileIds: string[],
  fileNames: string[],
  message: string,
  sessionId: string
): Promise<ChatResponse> {
  const { data } = await api.post('/chat', { file_ids: fileIds, file_names: fileNames, message, session_id: sessionId })
  return data
}

export interface SSEEvent {
  type: 'activity' | 'token' | 'done' | 'error'
  text?: string
  content?: string
  output_files?: OutputFile[]
}

const WS_BASE = import.meta.env.DEV
  ? 'ws://localhost:8000'
  : `ws://${window.location.host}`

export async function* sendMessageStream(
  fileIds: string[],
  fileNames: string[],
  message: string,
  sessionId: string
): AsyncGenerator<SSEEvent> {
  const ws = new WebSocket(`${WS_BASE}/chat/ws`)

  const queue: Array<SSEEvent | null> = []
  let notify: (() => void) | null = null

  const push = (item: SSEEvent | null) => {
    queue.push(item)
    if (notify) { notify(); notify = null }
  }

  ws.onopen = () => {
    ws.send(JSON.stringify({ file_ids: fileIds, file_names: fileNames, message, session_id: sessionId }))
  }
  ws.onmessage = (e) => {
    try { push(JSON.parse(e.data as string)) } catch { /* ignore */ }
  }
  ws.onerror = () => push({ type: 'error', text: 'WebSocket connection error' })
  ws.onclose = () => push(null)

  while (true) {
    if (queue.length === 0) {
      await new Promise<void>(r => { notify = r })
    }
    const item = queue.shift()!
    if (item === null) break
    yield item
  }
}

export interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export async function getHistory(sessionId: string): Promise<HistoryMessage[]> {
  const { data } = await api.get(`/history/${sessionId}`)
  return data.messages ?? []
}

export function getDownloadUrl(filename: string): string {
  return `/download/${filename}`
}
