# 图标生成指南

## 问题解决

已修复以下错误：
```
Error while trying to use the following icon from the Manifest: http://localhost:5173/vite.svg (Download error or resource isn't a valid image)
```

## 已创建的文件

### Web 图标 (public/ 目录)
- `favicon.ico` - 主要网站图标 (SVG格式)
- `favicon-16x16.png` - 16x16 像素图标
- `favicon-32x32.png` - 32x32 像素图标  
- `apple-touch-icon.png` - 180x180 Apple Touch 图标
- `kk-stock-icon.svg` - 高质量 SVG 图标
- `vite.svg` - Vite 默认图标

### Web Manifest
- 更新了 `site.webmanifest` 以使用正确的图标路径
- 配置了多种尺寸的图标支持
- 设置了正确的主题色和背景色

## Electron 应用图标生成

要为 Electron 应用生成图标，需要创建以下文件：

### macOS
```bash
# 需要生成 icon.icns 文件
# 可以使用在线工具或以下命令：
# 1. 先将 kk-stock-icon.svg 转换为 1024x1024 的 PNG
# 2. 使用 iconutil 生成 .icns
```

### Windows  
```bash
# 需要生成 icon.ico 文件
# 可以使用在线工具将 PNG 转换为 ICO 格式
```

### Linux
```bash
# 需要生成 icon.png 文件 (512x512 推荐)
```

## 在线图标生成工具推荐

1. [RealFaviconGenerator](https://realfavicongenerator.net/) - 全面的 favicon 生成
2. [ICO Convert](https://icoconvert.com/) - ICO 格式转换
3. [CloudConvert](https://cloudconvert.com/) - 多格式转换

## 使用方法

1. 将 `public/kk-stock-icon.svg` 上传到在线工具
2. 生成所需格式的图标文件
3. 将生成的文件放到 `build/` 目录：
   - `build/icon.icns` (macOS)
   - `build/icon.ico` (Windows)  
   - `build/icon.png` (Linux)

## 验证修复

启动开发服务器后，应该不再出现图标加载错误：
```bash
npm run dev
```

浏览器标签页和 PWA manifest 现在应该能正确显示图标。