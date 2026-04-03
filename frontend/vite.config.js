import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/drug': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/payments': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/prescription': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/make_payment': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/prescribe': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/consultation-api': {
        target:
          'https://personal-wv4mxqur.outsystemscloud.com/RecordVisitNotes/rest/ConsultationAPI',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/consultation-api/, ''),
      },
    },
  },
})