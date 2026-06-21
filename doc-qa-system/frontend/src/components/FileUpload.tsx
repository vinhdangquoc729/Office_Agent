import { useRef, useState } from 'react'
import { uploadFile } from '../api/client'

interface Props {
  onUploaded: (fileId: string, filename: string) => void
}

export default function FileUpload({ onUploaded }: Props) {
  const [uploading, setUploading] = useState(false)
  const [uploadedName, setUploadedName] = useState<string | null>(null)
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    setUploading(true)
    setError('')
    try {
      const { file_id, filename } = await uploadFile(file)
      setUploadedName(filename)
      onUploaded(file_id, filename)
    } catch {
      setError('Upload thất bại. Vui lòng thử lại.')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
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
        ) : uploadedName ? (
          <span style={styles.uploaded}>📎 {uploadedName} ✓</span>
        ) : (
          <span style={styles.hint}>Kéo thả file vào đây hoặc click để chọn<br />(PDF, XLSX, DOCX, MD)</span>
        )}
      </div>
      {error && <p style={styles.error}>{error}</p>}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.xlsx,.xls,.docx,.md"
        style={{ display: 'none' }}
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
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
  uploaded: { color: '#1a7f37', fontWeight: 600 },
  hint: { lineHeight: 1.6 },
  error: { color: '#cf222e', fontSize: 12, marginTop: 4 },
}
