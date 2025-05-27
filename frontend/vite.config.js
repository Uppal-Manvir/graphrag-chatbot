import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    proxy: {
      // any request to /query_api will be forwarded to port 8000
      '/query': {
        target: 'http://127.0.0.1:8000',
        
        changeOrigin: true,
        secure: false,
      },
      // If you ever use /api/query as your path, add:
      // '/api/query': { target: 'http://localhost:8000', changeOrigin: true },
    }
  }
})
