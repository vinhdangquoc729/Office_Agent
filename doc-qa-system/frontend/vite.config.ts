import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/upload':   'http://localhost:8000',
      '/download': 'http://localhost:8000',
      '/history':  'http://localhost:8000',
      '/chat': {
        target: 'http://localhost:8000',
        configure(proxy) {
          // Remove Accept-Encoding so backend sends plain text,
          // preventing Vite's compression middleware from buffering SSE.
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.removeHeader('accept-encoding')
          })
        },
      },
    },
  },
})
