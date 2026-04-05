import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
    server: {
      proxy: {
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
