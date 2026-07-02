import { useRef, useState } from 'react'
import { uploadFile } from '../api/client'
import { useLanguage } from '../i18n'

export interface UploadedFile {
  fileId: string
  filename: string
}

interface Props {
  onUploaded: (files: UploadedFile[]) => void
}

export default function FileUpload({ onUploaded }: Props) {
  const { t } = useLanguage()
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
      setError(t('uploadFailed'))
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
          <span>{t('uploading')}</span>
        ) : uploadedFiles.length > 0 ? (
          <div style={styles.fileList}>
            {uploadedFiles.map((f) => (
              <span key={f.fileId} style={styles.uploaded}>📎 {f.filename} ✓</span>
            ))}
            <span style={styles.addHint}>{t('addFile')}</span>
          </div>
        ) : (
          <span style={styles.hint}>{t('dropHint').split('\n').map((line, i) => (
            i === 0 ? <>{line}<br /></> : line
          ))}</span>
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
    border: '1px dashed var(--border)',
    borderRadius: 10,
    padding: '14px 16px',
    cursor: 'pointer',
    textAlign: 'center',
    fontSize: 13,
    color: 'var(--text-1)',
    background: 'var(--bg-elevated)',
    transition: 'border-color 0.2s, background 0.2s',
  },
  fileList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    alignItems: 'flex-start',
    textAlign: 'left',
  },
  uploaded: { color: 'var(--success)', fontWeight: 500, fontSize: 13 },
  addHint: { color: 'var(--accent-text)', fontSize: 12, marginTop: 6 },
  hint: { lineHeight: 1.7, color: 'var(--text-2)' },
  error: { color: 'var(--error)', fontSize: 12, marginTop: 4 },
}
