import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  // Client ID de Google (publico por diseño) -- hardcodeado aca porque las variables
  // VITE_* no se estaban propagando al build en Vercel por algun problema de cacheo
  // que no logramos diagnosticar desde afuera; esto lo evita por completo.
  define: {
    'import.meta.env.VITE_GOOGLE_CLIENT_ID': JSON.stringify('536024229438-vu5535528ilo10btk0dhg8hlluh6oqen.apps.googleusercontent.com'),
  },
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
