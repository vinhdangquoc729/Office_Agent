import { getDownloadUrl, OutputFile } from '../api/client'

interface Props {
  files: OutputFile[]
}

const icons: Record<string, string> = { report: '📄', slide: '📊' }
const labels: Record<string, string> = { report: 'Báo cáo .docx', slide: 'Slide .pptx' }

export default function DownloadButton({ files }: Props) {
  if (!files.length) return null
  return (
    <div style={styles.container}>
      {files.map((f) => (
        <a key={f.id} href={getDownloadUrl(f.id)} download={f.name} style={styles.btn}>
          {icons[f.type] ?? '📁'} Tải {labels[f.type] ?? f.name}
        </a>
      ))}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: { display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' },
  btn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    padding: '5px 12px',
    background: '#0969da',
    color: '#fff',
    borderRadius: 6,
    fontSize: 13,
    textDecoration: 'none',
    fontWeight: 500,
  },
}
