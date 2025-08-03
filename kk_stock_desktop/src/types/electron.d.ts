// Electron API类型定义
export interface ElectronAPI {
  // 应用相关
  getVersion: () => Promise<string>
  getPath: (name: string) => Promise<string>
  quit: () => void
  
  // 窗口相关
  minimize: () => void
  maximize: () => void
  unmaximize: () => void
  close: () => void
  isMaximized: () => Promise<boolean>
  toggleMaximize: () => Promise<boolean>
  
  // 对话框
  showMessageBox: (options: {
    type?: 'none' | 'info' | 'error' | 'question' | 'warning'
    buttons?: string[]
    defaultId?: number
    title?: string
    message: string
    detail?: string
  }) => Promise<{ response: number; checkboxChecked: boolean }>
  
  showSaveDialog: (options: {
    title?: string
    defaultPath?: string
    buttonLabel?: string
    filters?: Array<{ name: string; extensions: string[] }>
  }) => Promise<{ canceled: boolean; filePath?: string }>
  
  showOpenDialog: (options: {
    title?: string
    defaultPath?: string
    buttonLabel?: string
    filters?: Array<{ name: string; extensions: string[] }>
    properties?: Array<'openFile' | 'openDirectory' | 'multiSelections' | 'showHiddenFiles'>
  }) => Promise<{ canceled: boolean; filePaths: string[] }>
  
  // 文件系统
  writeFile: (filePath: string, data: string) => Promise<void>
  readFile: (filePath: string) => Promise<string>
  existsFile: (filePath: string) => Promise<boolean>
  
  // 菜单事件
  onMenuAction: (callback: (action: string, data?: any) => void) => void
  removeMenuListener: (callback: () => void) => void
  
  // 系统信息
  getSystemInfo: () => Promise<{
    platform: string
    arch: string
    version: string
    totalMemory: number
    freeMemory: number
  }>
  
  // 网络
  checkNetworkConnection: () => Promise<boolean>
  
  // 进程管理
  execCommand: (command: string) => Promise<{ stdout: string; stderr: string }>
  
  // 通知
  showNotification: (title: string, body: string) => void
  
  // 更新相关
  checkForUpdates: () => Promise<boolean>
  downloadUpdate: () => Promise<void>
  installUpdate: () => void
  
  // 开发者工具
  toggleDevTools: () => void
  
  // 主题
  getNativeTheme: () => Promise<'system' | 'light' | 'dark'>
  setNativeTheme: (theme: 'system' | 'light' | 'dark') => void
  
  // 事件监听
  on: (event: string, callback: (...args: any[]) => void) => void
  off: (event: string, callback: (...args: any[]) => void) => void
  
  // 存储
  store: {
    get: (key: string) => Promise<any>
    set: (key: string, value: any) => Promise<void>
    delete: (key: string) => Promise<void>
    clear: () => Promise<void>
  }
  
  // AI提示词管理
  updateSystemPrompt?: (prompt: string) => void
}

// 全局声明
declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}

export { ElectronAPI }