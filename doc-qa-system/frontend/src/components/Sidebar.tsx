import { Conversation } from '../App'
import { useLanguage } from '../i18n'
import gbFlag from '../../res/gb.webp'
import vnFlag from '../../res/vn.webp'

interface Props {
  conversations: Conversation[]
  activeConvId: string | null
  onSelect: (id: string) => void
  onNewChat: () => void
}

export default function Sidebar({ conversations, activeConvId, onSelect, onNewChat }: Props) {
  const { lang, setLang, t } = useLanguage()

  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <span style={styles.logo}>📑</span>
        <span style={styles.brand}>Doc-QA</span>
        <div style={styles.langSwitch}>
          <button
            style={{ ...styles.flagBtn, opacity: lang === 'vi' ? 1 : 0.28 }}
            onClick={() => setLang('vi')}
            title="Tiếng Việt"
          >
            <img src={vnFlag} alt="VI" style={styles.flagImg} />
          </button>
          <button
            style={{ ...styles.flagBtn, opacity: lang === 'en' ? 1 : 0.28 }}
            onClick={() => setLang('en')}
            title="English"
          >
            <img src={gbFlag} alt="EN" style={styles.flagImg} />
          </button>
        </div>
      </div>

      <button style={styles.newBtn} onClick={onNewChat}>
        <span style={styles.newBtnPlus}>+</span> {t('newChat')}
      </button>

      <div style={styles.sectionLabel}>{t('conversations')}</div>

      <div style={styles.list}>
        {conversations.length === 0 && (
          <p style={styles.empty}>{t('noConversations')}</p>
        )}
        {conversations.map((c) => (
          <button
            key={c.id}
            style={{ ...styles.item, ...(c.id === activeConvId ? styles.itemActive : {}) }}
            onClick={() => onSelect(c.id)}
          >
            <div style={styles.itemTitle}>{c.title}</div>
            <div style={styles.itemSub}>{c.files?.map((f: { name: string }) => f.name).join(', ') ?? ''}</div>
          </button>
        ))}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: 256,
    background: '#111111',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    flexShrink: 0,
    borderRight: '1px solid #222',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '18px 14px 10px',
  },
  logo: { fontSize: 20 },
  brand: {
    fontSize: 15,
    fontWeight: 700,
    color: '#efefef',
    letterSpacing: 0.3,
    flex: 1,
  },
  langSwitch: {
    display: 'flex',
    gap: 2,
    marginLeft: 'auto',
    flexShrink: 0,
    alignItems: 'center',
  },
  flagBtn: {
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    padding: '2px 3px',
    borderRadius: 4,
    lineHeight: 1,
    transition: 'opacity 0.15s',
    display: 'flex',
    alignItems: 'center',
  },
  flagImg: {
    width: 22,
    height: 16,
    objectFit: 'cover',
    borderRadius: 2,
    display: 'block',
  },
  newBtn: {
    margin: '4px 10px 10px',
    padding: '8px 12px',
    background: 'transparent',
    border: '1px solid #2e2e2e',
    borderRadius: 8,
    color: '#d0d0d0',
    fontSize: 13,
    cursor: 'pointer',
    textAlign: 'left',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    transition: 'border-color 0.15s, background 0.15s',
  },
  newBtnPlus: {
    fontSize: 16,
    lineHeight: 1,
    color: '#666',
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: 600,
    color: '#444',
    textTransform: 'uppercase',
    letterSpacing: 1,
    padding: '4px 14px 6px',
  },
  list: {
    flex: 1,
    overflowY: 'auto',
    padding: '0 6px 12px',
  },
  empty: {
    fontSize: 12,
    color: '#444',
    textAlign: 'center',
    padding: '20px 0',
  },
  item: {
    width: '100%',
    padding: '9px 10px',
    borderRadius: 7,
    cursor: 'pointer',
    marginBottom: 1,
    background: 'transparent',
    border: 'none',
    textAlign: 'left',
    display: 'block',
    transition: 'background 0.1s',
  },
  itemActive: {
    background: '#1e1e1e',
  },
  itemTitle: {
    fontSize: 13,
    color: '#d8d8d8',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  itemSub: {
    fontSize: 11,
    color: '#555',
    marginTop: 2,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
}
