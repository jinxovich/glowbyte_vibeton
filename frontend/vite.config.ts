import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Позволяет доступ по IP (важно для докера и иногда для локалки)
    port: 5173,
  }
})