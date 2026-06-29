import { Conversation } from '../App'

interface Props {
  conversations: Conversation[]
  activeConvId: string | null
  onSelect: (id: string) => void
  onNewChat: () => void
}

export default function Sidebar({ conversations, activeConvId, onSelect, onNewChat }: Props) {
  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <span style={styles.logo}>📑</span>
        <span style={styles.brand}>Doc-QA</span>
      </div>

      <button style={styles.newBtn} onClick={onNewChat}>
        <span style={styles.newBtnPlus}>+</span> Chat mới
      </button>

      <div style={styles.sectionLabel}>Hội thoại</div>

      <div style={styles.list}>
        {conversations.length === 0 && (
          <p style={styles.empty}>Chưa có hội thoại nào</p>
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
    background: '#171717',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    flexShrink: 0,
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
    color: '#ececec',
    letterSpacing: 0.3,
  },
  newBtn: {
    margin: '4px 10px 10px',
    padding: '8px 12px',
    background: 'transparent',
    border: '1px solid #3a3a3a',
    borderRadius: 8,
    color: '#ececec',
    fontSize: 13,
    cursor: 'pointer',
    textAlign: 'left',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  newBtnPlus: {
    fontSize: 16,
    lineHeight: 1,
    color: '#a0a0a0',
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: '#555',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    padding: '4px 14px 6px',
  },
  list: {
    flex: 1,
    overflowY: 'auto',
    padding: '0 6px 12px',
  },
  empty: {
    fontSize: 12,
    color: '#555',
    textAlign: 'center',
    padding: '20px 0',
  },
  item: {
    width: '100%',
    padding: '9px 10px',
    borderRadius: 8,
    cursor: 'pointer',
    marginBottom: 2,
    background: 'transparent',
    border: 'none',
    textAlign: 'left',
    display: 'block',
  },
  itemActive: {
    background: '#2a2a2a',
  },
  itemTitle: {
    fontSize: 13,
    color: '#ddd',
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
