import React, { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'

export type Lang = 'vi' | 'en'

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
  },
}

export type TranslationKey = keyof typeof TRANSLATIONS.vi

interface LangContext {
  lang: Lang
  setLang: (l: Lang) => void
  t: (key: TranslationKey, vars?: Record<string, string>) => string
}

const LanguageContext = createContext<LangContext>({
  lang: 'vi',
  setLang: () => {},
  t: (key) => TRANSLATIONS.vi[key],
})

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(
    () => (localStorage.getItem('doc_qa_lang') as Lang) ?? 'vi'
  )

  const setLang = (l: Lang) => {
    setLangState(l)
    localStorage.setItem('doc_qa_lang', l)
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

  return React.createElement(LanguageContext.Provider, { value: { lang, setLang, t } }, children)
}

export const useLanguage = () => useContext(LanguageContext)
