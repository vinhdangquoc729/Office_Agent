import axios from 'axios'

const api = axios.create({ baseURL: '/' })

export interface OutputFile {
  id: string
  name: string
  type: 'report' | 'slide'
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
  fileId: string,
  message: string,
  sessionId: string
): Promise<ChatResponse> {
  const { data } = await api.post('/chat', { file_id: fileId, message, session_id: sessionId })
  return data
}

export interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export async function getHistory(sessionId: string, fileId: string): Promise<HistoryMessage[]> {
  const { data } = await api.get(`/history/${sessionId}/${fileId}`)
  return data.messages ?? []
}

export function getDownloadUrl(filename: string): string {
  return `/download/${filename}`
}
