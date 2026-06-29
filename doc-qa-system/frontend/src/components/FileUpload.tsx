import { useRef, useState } from 'react'
import { uploadFile } from '../api/client'

export interface UploadedFile {
  fileId: string
  filename: string
}

interface Props {
  onUploaded: (files: UploadedFile[]) => void
}

export default function FileUpload({ onUploaded }: Props) {
  const [uploading, setUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = async (fileList: FileList | File[]) => {
    const files = Array.from(fileList)
    if (!files.length) return
    setUploading(true)
    setError('')
    try {
      const results: UploadedFile[] = []
      for (const file of files) {
        const { file_id, filename } = await uploadFile(file)
        results.push({ fileId: file_id, filename })
      }
      const merged = [...uploadedFiles, ...results]
      setUploadedFiles(merged)
      onUploaded(merged)
    } catch {
      setError('Upload thất bại. Vui lòng thử lại.')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files)
  }

  return (
    <div style={styles.wrapper}>
      <div
        style={styles.dropzone}
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
      >
        {uploading ? (
          <span>Đang upload...</span>
        ) : uploadedFiles.length > 0 ? (
          <div style={styles.fileList}>
            {uploadedFiles.map((f) => (
              <span key={f.fileId} style={styles.uploaded}>📎 {f.filename} ✓</span>
            ))}
            <span style={styles.addHint}>+ Thêm file</span>
          </div>
        ) : (
          <span style={styles.hint}>Kéo thả file vào đây hoặc click để chọn<br />(PDF, XLSX, DOCX, MD — hỗ trợ nhiều file)</span>
        )}
      </div>
      {error && <p style={styles.error}>{error}</p>}
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.xlsx,.xls,.docx,.md"
        style={{ display: 'none' }}
        onChange={(e) => e.target.files && handleFiles(e.target.files)}
      />
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: { padding: '8px 12px' },
  dropzone: {
    border: '2px dashed #d0d7de',
    borderRadius: 8,
    padding: '12px 16px',
    cursor: 'pointer',
    textAlign: 'center',
    fontSize: 13,
    color: '#666',
    background: '#fafafa',
    transition: 'border-color 0.2s',
  },
  fileList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    alignItems: 'flex-start',
    textAlign: 'left',
  },
  uploaded: { color: '#1a7f37', fontWeight: 600 },
  addHint: { color: '#0969da', fontSize: 12, marginTop: 4 },
  hint: { lineHeight: 1.6 },
  error: { color: '#cf222e', fontSize: 12, marginTop: 4 },
}
