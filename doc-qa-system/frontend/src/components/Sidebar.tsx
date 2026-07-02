import { useState } from 'react'
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

function SettingsPanel({ onClose }: { onClose: () => void }) {
  const { lang, setLang, theme, setTheme, t } = useLanguage()
  return (
    <>
      <div style={styles.backdrop} onClick={onClose} />
      <div style={styles.panel}>
        <div style={styles.panelSection}>
          <span style={styles.panelLabel}>{t('langLabel')}</span>
          <div style={styles.panelRow}>
            {(['vi', 'en'] as const).map((l) => (
              <button
                key={l}
                style={{ ...styles.optionBtn, ...(lang === l ? styles.optionBtnActive : {}) }}
                onClick={() => setLang(l)}
              >
                <img
                  src={l === 'vi' ? vnFlag : gbFlag}
                  alt={l}
                  style={styles.flagImg}
                />
                {l === 'vi' ? 'Tiếng Việt' : 'English'}
              </button>
            ))}
          </div>
        </div>

        <div style={styles.panelDivider} />

        <div style={styles.panelSection}>
          <span style={styles.panelLabel}>{t('themeLabel')}</span>
          <div style={styles.panelRow}>
            <button
              style={{ ...styles.optionBtn, ...(theme === 'light' ? styles.optionBtnActive : {}) }}
              onClick={() => setTheme('light')}
            >
              ☀ {t('themeLight')}
            </button>
            <button
              style={{ ...styles.optionBtn, ...(theme === 'dark' ? styles.optionBtnActive : {}) }}
              onClick={() => setTheme('dark')}
            >
              ◑ {t('themeDark')}
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

export default function Sidebar({ conversations, activeConvId, onSelect, onNewChat }: Props) {
  const { t } = useLanguage()
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <span style={styles.logo}>📑</span>
        <span style={styles.brand}>Doc-QA</span>
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

      {/* Settings button anchored to bottom */}
      <div style={styles.bottomBar}>
        {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
        <button
          style={{ ...styles.settingsBtn, ...(settingsOpen ? styles.settingsBtnOpen : {}) }}
          onClick={() => setSettingsOpen((v) => !v)}
          title={t('settingsBtn')}
        >
          <span style={styles.settingsIcon}>⚙</span>
          <span>{t('settingsBtn')}</span>
        </button>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: 256,
    background: 'var(--bg-surface)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    flexShrink: 0,
    borderRight: '1px solid var(--border-subtle)',
    position: 'relative',
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
    color: 'var(--text-0)',
    letterSpacing: 0.3,
    flex: 1,
  },
  newBtn: {
    margin: '4px 10px 10px',
    padding: '8px 12px',
    background: 'transparent',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text-0)',
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
    color: 'var(--text-2)',
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: 600,
    color: 'var(--text-2)',
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
    color: 'var(--text-2)',
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
  },
  itemActive: {
    background: 'var(--bg-elevated)',
  },
  itemTitle: {
    fontSize: 13,
    color: 'var(--text-0)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  itemSub: {
    fontSize: 11,
    color: 'var(--text-2)',
    marginTop: 2,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },

  // ── Bottom settings button ──────────────────────────────
  bottomBar: {
    flexShrink: 0,
    padding: '8px 8px 10px',
    borderTop: '1px solid var(--border-subtle)',
    position: 'relative',
  },
  settingsBtn: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '8px 12px',
    background: 'transparent',
    border: 'none',
    borderRadius: 7,
    color: 'var(--text-1)',
    fontSize: 13,
    cursor: 'pointer',
    textAlign: 'left',
  },
  settingsBtnOpen: {
    background: 'var(--bg-elevated)',
    color: 'var(--text-0)',
  },
  settingsIcon: {
    fontSize: 15,
    opacity: 0.7,
  },

  // ── Settings panel (popup) ──────────────────────────────
  backdrop: {
    position: 'fixed',
    inset: 0,
    zIndex: 99,
  },
  panel: {
    position: 'absolute',
    bottom: 52,
    left: 8,
    right: 8,
    zIndex: 100,
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 10,
    padding: '4px 0',
    boxShadow: 'var(--shadow-panel)',
  },
  panelSection: {
    padding: '10px 14px',
  },
  panelLabel: {
    fontSize: 10,
    fontWeight: 600,
    color: 'var(--text-2)',
    textTransform: 'uppercase',
    letterSpacing: 0.9,
    display: 'block',
    marginBottom: 8,
  },
  panelRow: {
    display: 'flex',
    gap: 6,
  },
  panelDivider: {
    height: 1,
    background: 'var(--border)',
    margin: '0 14px',
  },
  optionBtn: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: '6px 8px',
    background: 'transparent',
    border: '1px solid var(--border)',
    borderRadius: 6,
    color: 'var(--text-1)',
    fontSize: 12,
    cursor: 'pointer',
    fontWeight: 500,
  },
  optionBtnActive: {
    background: 'var(--accent-bg)',
    borderColor: 'var(--accent-border)',
    color: 'var(--accent-text)',
  },
  flagImg: {
    width: 18,
    height: 13,
    objectFit: 'cover',
    borderRadius: 2,
    display: 'block',
  },
}
