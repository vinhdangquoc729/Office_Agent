import React, { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'

export type Lang = 'vi' | 'en'
export type Theme = 'light' | 'dark'

const TRANSLATIONS = {
  vi: {
    newConversation: 'Hội thoại mới',
    uploadHint: 'Upload file để bắt đầu hội thoại mới (hỗ trợ nhiều file)',
    welcomeEmpty: 'Bạn muốn hỏi gì?',
    welcomeLoaded: 'Đã tải {names}. Bạn muốn hỏi gì về tài liệu này?',
    connecting: 'Đang kết nối...',
    processDone: 'Xử lý hoàn tất.',
    errorPrefix: 'Lỗi: {text}',
    connError: 'Lỗi kết nối tới server.',
    downloadBtn: 'Tải xuống',
    downloadTitle: 'Tải xuống {name}',
    inputPlaceholder: 'Nhập yêu cầu... (Enter để gửi)',
    sendBtn: 'Gửi',
    uploadFailed: 'Upload thất bại. Vui lòng thử lại.',
    uploading: 'Đang upload...',
    addFile: '+ Thêm file',
    dropHint: 'Kéo thả file vào đây hoặc click để chọn\n(PDF, XLSX, DOCX, MD — hỗ trợ nhiều file)',
    newChat: 'Chat mới',
    conversations: 'Hội thoại',
    noConversations: 'Chưa có hội thoại nào',
    downloadReport: 'Báo cáo .docx',
    downloadSlide: 'Slide .pptx',
    downloadLink: 'Tải {label}',
    downloadImage: 'Tải ảnh',
    langToggle: 'EN',
    settingsBtn: 'Cài đặt',
    langLabel: 'Ngôn ngữ',
    themeLabel: 'Giao diện',
    themeLight: 'Sáng',
    themeDark: 'Tối',
  },
  en: {
    newConversation: 'New conversation',
    uploadHint: 'Upload a file to start a new conversation (supports multiple files)',
    welcomeEmpty: 'What would you like to ask?',
    welcomeLoaded: 'Loaded {names}. What would you like to know about this document?',
    connecting: 'Connecting...',
    processDone: 'Processing complete.',
    errorPrefix: 'Error: {text}',
    connError: 'Server connection error.',
    downloadBtn: 'Download',
    downloadTitle: 'Download {name}',
    inputPlaceholder: 'Type your request... (Enter to send)',
    sendBtn: 'Send',
    uploadFailed: 'Upload failed. Please try again.',
    uploading: 'Uploading...',
    addFile: '+ Add file',
    dropHint: 'Drag and drop files here or click to select\n(PDF, XLSX, DOCX, MD — supports multiple files)',
    newChat: 'New chat',
    conversations: 'Conversations',
    noConversations: 'No conversations yet',
    downloadReport: 'Report .docx',
    downloadSlide: 'Slide .pptx',
    downloadLink: 'Download {label}',
    downloadImage: 'Download image',
    langToggle: 'VI',
    settingsBtn: 'Settings',
    langLabel: 'Language',
    themeLabel: 'Theme',
    themeLight: 'Light',
    themeDark: 'Dark',
  },
}

export type TranslationKey = keyof typeof TRANSLATIONS.vi

interface LangContext {
  lang: Lang
  setLang: (l: Lang) => void
  t: (key: TranslationKey, vars?: Record<string, string>) => string
  theme: Theme
  setTheme: (t: Theme) => void
}

const LanguageContext = createContext<LangContext>({
  lang: 'vi',
  setLang: () => {},
  t: (key) => TRANSLATIONS.vi[key],
  theme: 'dark',
  setTheme: () => {},
})

function applyThemeClass(t: Theme) {
  if (t === 'light') document.documentElement.classList.add('theme-light')
  else document.documentElement.classList.remove('theme-light')
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(
    () => (localStorage.getItem('doc_qa_lang') as Lang) ?? 'vi'
  )

  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = (localStorage.getItem('doc_qa_theme') as Theme) ?? 'dark'
    applyThemeClass(saved)
    return saved
  })

  const setLang = (l: Lang) => {
    setLangState(l)
    localStorage.setItem('doc_qa_lang', l)
  }

  const setTheme = (t: Theme) => {
    setThemeState(t)
    localStorage.setItem('doc_qa_theme', t)
    applyThemeClass(t)
  }

  const t = (key: TranslationKey, vars?: Record<string, string>): string => {
    let text =
      (TRANSLATIONS[lang] as Record<string, string>)[key] ??
      (TRANSLATIONS.vi as Record<string, string>)[key] ??
      key
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        text = text.replace(`{${k}}`, v)
      }
    }
    return text
  }

  return React.createElement(
    LanguageContext.Provider,
    { value: { lang, setLang, t, theme, setTheme } },
    children
  )
}

export const useLanguage = () => useContext(LanguageContext)
