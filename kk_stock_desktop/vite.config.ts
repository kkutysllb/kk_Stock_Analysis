import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types'),
      '@assets': resolve(__dirname, 'src/assets'),
      '@config': resolve(__dirname, 'src/config')
    }
  },
  base: './',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          element: ['element-plus'],
          charts: ['echarts', 'vue-echarts']
        }
      }
    }
  },
  server: {
    port: parseInt(env.VITE_DEV_PORT) || 5173,
    host: env.VITE_DEV_HOST === 'true' || true,
    open: env.VITE_DEV_OPEN === 'true' || false,
    hmr: {
      overlay: true
    },
    cors: true
  },
  css: {
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer')
      ]
    }
  },
  
  // 环境变量配置
  define: {
    __APP_VERSION__: JSON.stringify(env.VITE_APP_VERSION || '1.0.0'),
    // __API_BASE_URL__: JSON.stringify(env.VITE_API_BASE_URL || 'http://f1.ttyt.cc:41726')
    __API_BASE_URL__: JSON.stringify(env.VITE_API_BASE_URL || 'http://127.0.0.1:9001')
  }
  }
})