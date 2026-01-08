import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allow external connections (needed for Docker)
    port: 3000,
    proxy: {
      '/api': {
        // In Docker, Vite proxy runs in container, so use backend service name
        // For local dev, use localhost
        target: process.env.VITE_API_BASE_URL || (process.env.DOCKER ? 'http://backend:8000' : 'http://localhost:8000'),
        changeOrigin: true,
      },
    },
  },
})
