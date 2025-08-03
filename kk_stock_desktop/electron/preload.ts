import { contextBridge, ipcRenderer } from 'electron'

// 自定义API接口
export interface ElectronAPI {
  // 应用信息
  getVersion(): Promise<string>
  
  // 对话框
  showMessageBox(options: any): Promise<any>
  showSaveDialog(options: any): Promise<any>
  showOpenDialog(options: any): Promise<any>
  
  // 窗口控制
  toggleMaximize(): Promise<boolean>
  
  // 菜单事件监听
  onMenuAction(callback: (action: string, data?: any) => void): void
  removeMenuListener(callback: (...args: any[]) => void): void
  
  // 导出功能
  onExportReport(callback: (filePath: string) => void): void
  removeExportListener(callback: (...args: any[]) => void): void
}

// 定义暴露给渲染进程的API
const electronAPI: ElectronAPI = {
  // 获取应用版本
  getVersion: () => ipcRenderer.invoke('app-version'),
  
  // 对话框相关
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  
  // 窗口控制
  toggleMaximize: () => ipcRenderer.invoke('toggle-maximize'),
  
  // 菜单事件监听
  onMenuAction: (callback) => {
    const menuEvents = [
      'menu-new-analysis',
      'menu-settings',
      'menu-daily-analysis', 
      'menu-weekly-analysis',
      'menu-monthly-analysis',
      'menu-refresh-data',
      'menu-generate-xiaohongshu',
      'menu-generate-toutiao',
      'menu-generate-wechat',
      'menu-dashboard',
      'menu-charts'
    ]
    
    menuEvents.forEach(event => {
      ipcRenderer.on(event, (_, data) => callback(event, data))
    })
  },
  
  removeMenuListener: (callback) => {
    ipcRenderer.removeListener('menu-action', callback)
  },
  
  // 导出报告监听
  onExportReport: (callback) => {
    ipcRenderer.on('export-report', (_, filePath) => callback(filePath))
  },
  
  removeExportListener: (callback) => {
    ipcRenderer.removeListener('export-report', callback)
  }
}

// 使用 contextBridge 安全地暴露API
contextBridge.exposeInMainWorld('electronAPI', electronAPI)

// 类型声明，用于TypeScript支持
declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
} 