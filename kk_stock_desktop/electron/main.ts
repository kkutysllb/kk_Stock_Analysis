import { app, BrowserWindow, Menu, shell, ipcMain, dialog } from 'electron'
import { join } from 'path'

// 简单的 is 对象替代
const is = {
  dev: process.env.NODE_ENV === 'development' || !app.isPackaged
}

class Application {
  private mainWindow: BrowserWindow | null = null

  constructor() {
    this.init()
  }

  private init(): void {
    // 应用就绪时创建窗口
    app.whenReady().then(() => {
      app.setAppUserModelId('com.kk.stock-analysis')
      
      // 设置安全策略
      app.on('web-contents-created', (_, contents) => {
        contents.setWindowOpenHandler((details) => {
          const parsedUrl = new URL(details.url)
          if (parsedUrl.origin !== 'http://localhost:5173') {
            return { action: 'deny' }
          }
          return { action: 'allow' }
        })
      })

      this.createWindow()
      this.setupMenu()
      this.setupIPC()

      app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) this.createWindow()
      })
    })

    // 所有窗口关闭时退出应用 (macOS除外)
    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') app.quit()
    })
  }

  private createWindow(): void {
    // 创建主窗口
    this.mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 1200,
      minHeight: 800,
      show: false,
      autoHideMenuBar: false,
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
      icon: join(__dirname, '../build/icon.png'),
      webPreferences: {
        preload: join(__dirname, 'preload.js'),
        sandbox: false,
        nodeIntegration: false,
        contextIsolation: true,
        webSecurity: true
      }
    })

    // 窗口准备显示时显示
    this.mainWindow.on('ready-to-show', () => {
      this.mainWindow?.show()
      
      // 开发环境下打开调试工具
      if (is.dev) {
        this.mainWindow?.webContents.openDevTools()
      }
    })

    // 处理外部链接
    this.mainWindow.webContents.setWindowOpenHandler((details) => {
      shell.openExternal(details.url)
      return { action: 'deny' }
    })

    // 加载应用
    if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
      this.mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
    } else {
      this.mainWindow.loadFile(join(__dirname, '../dist/index.html'))
    }

    // 优化窗口性能
    if (is.dev) {
      this.mainWindow.webContents.on('before-input-event', (_, input) => {
        if (input.key === 'F12') {
          this.mainWindow?.webContents.toggleDevTools()
        }
        if (input.key === 'F5' || (input.control && input.key === 'r')) {
          this.mainWindow?.reload()
        }
      })
    }
  }

  private setupMenu(): void {
    const template = [
      {
        label: '文件',
        submenu: [
          {
            label: '新建分析',
            accelerator: 'CmdOrCtrl+N',
            click: () => this.mainWindow?.webContents.send('menu-new-analysis')
          },
          {
            label: '导出报告',
            accelerator: 'CmdOrCtrl+E',
            click: () => this.handleExportReport()
          },
          { type: 'separator' },
          {
            label: '设置',
            accelerator: 'CmdOrCtrl+,',
            click: () => this.mainWindow?.webContents.send('menu-settings')
          },
          { type: 'separator' },
          {
            label: '退出',
            accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
            click: () => app.quit()
          }
        ]
      },
      {
        label: '分析',
        submenu: [
          {
            label: '日评分析',
            accelerator: 'CmdOrCtrl+1',
            click: () => this.mainWindow?.webContents.send('menu-daily-analysis')
          },
          {
            label: '周评分析',
            accelerator: 'CmdOrCtrl+2',
            click: () => this.mainWindow?.webContents.send('menu-weekly-analysis')
          },
          {
            label: '月评分析',
            accelerator: 'CmdOrCtrl+3',
            click: () => this.mainWindow?.webContents.send('menu-monthly-analysis')
          },
          { type: 'separator' },
          {
            label: '刷新数据',
            accelerator: 'F5',
            click: () => this.mainWindow?.webContents.send('menu-refresh-data')
          }
        ]
      },
      // 智能收评内容生成菜单已删除
      {
        label: '视图',
        submenu: [
          {
            label: '仪表板',
            accelerator: 'CmdOrCtrl+Shift+1',
            click: () => this.mainWindow?.webContents.send('menu-dashboard')
          },
          {
            label: '指数分析',
            accelerator: 'CmdOrCtrl+Shift+2', 
            click: () => this.mainWindow?.webContents.send('menu-charts')
          },
          { type: 'separator' },
          {
            label: '全屏',
            accelerator: process.platform === 'darwin' ? 'Ctrl+Cmd+F' : 'F11',
            click: () => {
              const focused = BrowserWindow.getFocusedWindow()
              if (focused) focused.setFullScreen(!focused.isFullScreen())
            }
          }
        ]
      },
      {
        label: '帮助',
        submenu: [
          {
            label: '关于 KK Stock Analysis',
            click: () => this.showAboutDialog()
          },
          {
            label: '检查更新',
            click: () => this.checkForUpdates()
          },
          { type: 'separator' },
          {
            label: '开发者工具',
            accelerator: 'F12',
            click: () => this.mainWindow?.webContents.toggleDevTools()
          }
        ]
      }
    ]

    const menu = Menu.buildFromTemplate(template as any)
    Menu.setApplicationMenu(menu)
  }

  private setupIPC(): void {
    // 处理来自渲染进程的消息
    ipcMain.handle('app-version', () => app.getVersion())
    ipcMain.handle('show-message-box', async (_, options) => {
      const result = await dialog.showMessageBox(this.mainWindow!, options)
      return result
    })
    ipcMain.handle('show-save-dialog', async (_, options) => {
      const result = await dialog.showSaveDialog(this.mainWindow!, options)
      return result
    })
    ipcMain.handle('show-open-dialog', async (_, options) => {
      const result = await dialog.showOpenDialog(this.mainWindow!, options)
      return result
    })
    
    // 处理窗口最大化/还原
    ipcMain.handle('toggle-maximize', () => {
      if (!this.mainWindow) return false
      
      if (this.mainWindow.isMaximized()) {
        this.mainWindow.unmaximize()
        return false
      } else {
        this.mainWindow.maximize()
        return true
      }
    })
  }

  private async handleExportReport(): Promise<void> {
    try {
      const result = await dialog.showSaveDialog(this.mainWindow!, {
        title: '导出分析报告',
        defaultPath: `股票分析报告_${new Date().toISOString().split('T')[0]}.pdf`,
        filters: [
          { name: 'PDF文件', extensions: ['pdf'] },
          { name: '所有文件', extensions: ['*'] }
        ]
      })

      if (!result.canceled && result.filePath) {
        this.mainWindow?.webContents.send('export-report', result.filePath)
      }
    } catch (error) {
      console.error('导出报告失败:', error)
    }
  }

  private showAboutDialog(): void {
    dialog.showMessageBox(this.mainWindow!, {
      type: 'info',
      title: '关于 KK Stock Analysis',
      message: 'KK股票量化分析系统',
      detail: `版本: ${app.getVersion()}\n专业的股票量化分析系统\n\n© 2024 KK StockQuant Analysis Team`,
      buttons: ['确定']
    })
  }

  private checkForUpdates(): void {
    // TODO: 实现自动更新检查
    dialog.showMessageBox(this.mainWindow!, {
      type: 'info',
      title: '检查更新',
      message: '当前已是最新版本',
      detail: `版本: ${app.getVersion()}`,
      buttons: ['确定']
    })
  }
}

// 启动应用
new Application()