import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src/main'),
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src/preload'),
      },
    },
  },
  renderer: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src/renderer'),
        '@/components': path.resolve(__dirname, './src/renderer/components'),
        '@/pages': path.resolve(__dirname, './src/renderer/pages'),
        '@/hooks': path.resolve(__dirname, './src/renderer/hooks'),
        '@/services': path.resolve(__dirname, './src/renderer/services'),
        '@/store': path.resolve(__dirname, './src/renderer/store'),
        '@/utils': path.resolve(__dirname, './src/renderer/utils'),
        '@/types': path.resolve(__dirname, './src/renderer/types'),
        '@/contexts': path.resolve(__dirname, './src/renderer/contexts'),
        '@/assets': path.resolve(__dirname, './src/renderer/assets'),
      },
    },
    plugins: [react()],
  },
})
