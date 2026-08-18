import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', port: 3000,
    proxy: { '/api': { target: 'http://backend:8000', changeOrigin: true } }
  },
  preview: {
    host: '0.0.0.0', port: 4173,
    // el mundo del ROBOT UI: vite preview + uvicorn local
    proxy: { '/api': { target: process.env.ROBOT_API || 'http://127.0.0.1:8000', changeOrigin: true } }
  }
})
