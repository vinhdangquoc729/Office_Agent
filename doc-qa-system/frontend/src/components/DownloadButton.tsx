import { getDownloadUrl, OutputFile } from '../api/client'
import { useLanguage } from '../i18n'

interface Props {
  files: OutputFile[]
}

const icons: Record<string, string> = { report: '📄', slide: '📊' }

export default function DownloadButton({ files }: Props) {
  const { t } = useLanguage()
  const labels: Record<string, string> = { report: t('downloadReport'), slide: t('downloadSlide') }
  if (!files.length) return null
  return (
    <div style={styles.container}>
      {files.map((f) => (
        <a key={f.id} href={getDownloadUrl(f.id)} download={f.name} style={styles.btn}>
          {icons[f.type] ?? '📁'} {t('downloadLink', { label: labels[f.type] ?? f.name })}
        </a>
      ))}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: { display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' },
  btn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    padding: '5px 13px',
    background: 'var(--accent-bg)',
    color: 'var(--accent-text)',
    borderRadius: 6,
    fontSize: 13,
    textDecoration: 'none',
    fontWeight: 500,
    border: '1px solid var(--accent-border)',
  },
}
