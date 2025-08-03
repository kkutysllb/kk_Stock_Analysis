/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_DEV_PORT?: string
  readonly VITE_DEV_HOST?: string
  readonly VITE_DEV_OPEN?: string
  readonly VITE_APP_TITLE?: string
  readonly VITE_APP_VERSION?: string
  readonly VITE_DEBUG?: string
  readonly VITE_LOG_LEVEL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 