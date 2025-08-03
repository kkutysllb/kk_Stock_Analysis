# KK股票量化分析系统 - 配置管理说明

## 📋 概述

本项目采用统一的配置管理系统，通过环境变量和全局配置文件来管理所有API端点和应用设置。

## 🔧 配置文件结构

```
desktop-app/
├── .env                    # 基础环境变量
├── .env.development        # 开发环境配置
├── .env.production         # 生产环境配置
└── src/config/index.ts     # TypeScript配置管理
```

## 🌐 API端点配置

### 当前配置
- **API服务器**: `172.16.20.20:9000`
- **协议**: HTTP
- **超时时间**: 30秒

### 修改API端点

1. **开发环境**: 编辑 `.env.development`
```bash
VITE_API_BASE_URL=http://172.16.20.20:9000
```

2. **生产环境**: 编辑 `.env.production`
```bash
VITE_API_BASE_URL=http://172.16.20.20:9000
```

3. **全局默认**: 编辑 `.env`
```bash
VITE_API_BASE_URL=http://172.16.20.20:9000
```

## 🚀 开发环境启动

### 使用开发脚本

```bash
# 给脚本执行权限
chmod +x dev-frontend.sh

# 启动开发环境
./dev-frontend.sh

# 或者直接指定模式
./dev-frontend.sh web      # Web开发模式
./dev-frontend.sh electron # Electron开发模式
```

### 手动启动

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 启动Electron开发模式
npm run electron:dev
```

## 🔥 热重载功能

开发环境已配置完整的热重载功能：

- ✅ **HMR (Hot Module Replacement)**: 模块热替换
- ✅ **自动刷新**: 文件变化自动刷新页面
- ✅ **错误覆盖**: 编译错误显示在页面上
- ✅ **CORS支持**: 跨域请求支持

## 📝 配置使用示例

### 在代码中使用配置

```typescript
// 导入配置
import { CONFIG } from '@/config'

// 使用API配置
const apiUrl = CONFIG.API.BASE_URL
const timeout = CONFIG.API.TIMEOUT

// 使用应用配置
const appTitle = CONFIG.APP.TITLE
const version = CONFIG.APP.VERSION
```

### API客户端使用

```typescript
// 市场数据API
import { MarketAPI } from '@/api/market'
const marketApi = new MarketAPI() // 自动使用配置的API端点

// 内容生成API
import { ContentAPI } from '@/api/content'
const contentApi = new ContentAPI() // 自动使用配置的API端点
```

## 🛠️ 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | API服务器地址 | `http://172.16.20.20:9000` |
| `VITE_DEV_PORT` | 开发服务器端口 | `5173` |
| `VITE_DEV_HOST` | 开发服务器主机 | `true` |
| `VITE_DEV_OPEN` | 自动打开浏览器 | `false` |
| `VITE_APP_TITLE` | 应用标题 | `KK股票量化分析系统` |
| `VITE_APP_VERSION` | 应用版本 | `1.0.0` |
| `VITE_DEBUG` | 调试模式 | `false` |
| `VITE_LOG_LEVEL` | 日志级别 | `info` |

## 🔍 故障排除

### API连接问题

1. 检查API服务器是否运行:
```bash
curl http://172.16.20.20:9000/health
```

2. 检查网络连接:
```bash
ping 172.16.20.20
```

3. 检查防火墙设置

### 开发服务器问题

1. 端口被占用:
```bash
lsof -i :5173
```

2. 清除缓存:
```bash
rm -rf node_modules/.vite
npm run dev
```

### 热重载不工作

1. 检查文件监听限制:
```bash
# macOS
sudo sysctl -w kern.maxfiles=65536
sudo sysctl -w kern.maxfilesperproc=65536
```

2. 重启开发服务器:
```bash
./dev-frontend.sh
```

## 📞 技术支持

如有问题，请联系开发团队或查看项目文档。