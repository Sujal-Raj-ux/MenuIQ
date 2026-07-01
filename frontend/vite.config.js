import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/menu-matrix': 'http://127.0.0.1:8000',
      '/menu-analysis': 'http://127.0.0.1:8000',
      '/associations': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
