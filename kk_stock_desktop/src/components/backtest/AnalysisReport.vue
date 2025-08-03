<template>
  <div class="analysis-report">
    <el-card class="report-card">
      <template #header>
        <div class="report-header">
          <h3>策略分析报告</h3>
          <div class="report-actions">
            <el-button @click="exportReport" type="primary" size="small">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
            <el-button @click="printReport" size="small">
              <el-icon><Printer /></el-icon>
              打印报告
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="report-content" ref="reportRef">
        <div v-if="reportContent" v-html="renderedMarkdown" class="markdown-content"></div>
        <div v-else class="no-report">
          <el-empty description="暂无分析报告">
            <el-button type="primary" @click="generateReport">生成报告</el-button>
          </el-empty>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElCard, ElButton, ElIcon, ElEmpty, ElMessage } from 'element-plus'
import { Download, Printer } from '@element-plus/icons-vue'
import { marked } from 'marked'

interface Props {
  reportContent: string
}

const props = defineProps<Props>()

const reportRef = ref<HTMLElement>()

// 监听reportContent变化，添加调试信息
watch(() => props.reportContent, (newContent) => {
  console.log('📋 分析报告内容更新:', {
    hasContent: !!newContent,
    contentLength: newContent?.length || 0,
    contentPreview: newContent?.substring(0, 200) || '空内容'
  })
}, { immediate: true })

// 渲染Markdown内容
const renderedMarkdown = computed(() => {
  if (!props.reportContent) return ''
  
  // 配置marked选项
  marked.setOptions({
    breaks: true,
    gfm: true
  })
  
  return marked(props.reportContent)
})

const exportReport = () => {
  if (!props.reportContent) {
    ElMessage.warning('暂无报告内容可导出')
    return
  }
  
  // 创建Blob对象
  const blob = new Blob([props.reportContent], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  
  // 创建下载链接
  const link = document.createElement('a')
  link.href = url
  link.download = `回测分析报告_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  // 释放URL对象
  URL.revokeObjectURL(url)
  
  ElMessage.success('报告导出成功')
}

const printReport = () => {
  if (!reportRef.value) {
    ElMessage.warning('暂无报告内容可打印')
    return
  }
  
  // 创建打印窗口
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('无法打开打印窗口，请检查浏览器设置')
    return
  }
  
  // 获取当前页面的样式
  const styles = Array.from(document.styleSheets)
    .map(styleSheet => {
      try {
        return Array.from(styleSheet.cssRules)
          .map(rule => rule.cssText)
          .join('\n')
      } catch (e) {
        return ''
      }
    })
    .join('\n')
  
  // 构建打印页面HTML
  const printHTML = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>回测分析报告</title>
      <meta charset="utf-8">
      <style>
        ${styles}
        body { 
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          line-height: 1.6;
          color: #2c3e50;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        .markdown-content h1, .markdown-content h2, .markdown-content h3 {
          color: #2c3e50;
          border-bottom: 2px solid #3498db;
          padding-bottom: 10px;
        }
        .markdown-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 20px 0;
        }
        .markdown-content th, .markdown-content td {
          border: 1px solid #ddd;
          padding: 12px;
          text-align: left;
        }
        .markdown-content th {
          background-color: #f8f9fa;
          font-weight: bold;
        }
        @media print {
          body { margin: 0; }
          .report-actions { display: none; }
        }
      </style>
    </head>
    <body>
      ${reportRef.value.innerHTML}
    </body>
    </html>
  `
  
  printWindow.document.write(printHTML)
  printWindow.document.close()
  
  // 等待内容加载完成后打印
  printWindow.onload = () => {
    printWindow.print()
    printWindow.close()
  }
}

const generateReport = () => {
  ElMessage.info('报告生成功能开发中...')
  // TODO: 如果需要，可以触发重新获取报告的逻辑
}
</script>

<style scoped>
.analysis-report {
  width: 100%;
}

.report-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.report-card :deep(.el-card__header) {
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 16px 20px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.report-actions {
  display: flex;
  gap: 12px;
}

.report-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 20px 0;
}

.markdown-content {
  line-height: 1.8;
  color: var(--el-text-color-primary);
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  color: var(--el-text-color-primary);
  margin: 24px 0 16px 0;
  font-weight: 600;
}

.markdown-content :deep(h1) {
  font-size: 28px;
  border-bottom: 3px solid var(--el-color-primary);
  padding-bottom: 12px;
}

.markdown-content :deep(h2) {
  font-size: 24px;
  border-bottom: 2px solid var(--el-color-primary-light-3);
  padding-bottom: 10px;
}

.markdown-content :deep(h3) {
  font-size: 20px;
  border-bottom: 1px solid var(--el-color-primary-light-5);
  padding-bottom: 8px;
}

.markdown-content :deep(h4) {
  font-size: 18px;
  color: var(--el-color-primary);
}

.markdown-content :deep(p) {
  margin: 16px 0;
  text-align: justify;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--el-border-color-lighter);
  padding: 12px 16px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: var(--el-color-primary-light-9);
  font-weight: 600;
  color: var(--el-color-primary);
}

.markdown-content :deep(tr:nth-child(even)) {
  background: var(--el-fill-color-lighter);
}

.markdown-content :deep(tr:hover) {
  background: var(--el-color-primary-light-9);
}

.markdown-content :deep(strong) {
  color: var(--el-color-primary);
  font-weight: 600;
}

.markdown-content :deep(code) {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: var(--el-fill-color-light);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid var(--el-color-primary);
  padding-left: 16px;
  margin: 16px 0;
  color: var(--el-text-color-regular);
  background: var(--el-color-primary-light-9);
  padding: 16px;
  border-radius: 0 8px 8px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 20px;
  margin: 16px 0;
}

.markdown-content :deep(li) {
  margin: 8px 0;
}

.markdown-content :deep(hr) {
  border: none;
  height: 2px;
  background: linear-gradient(to right, transparent, var(--el-border-color), transparent);
  margin: 32px 0;
}

.no-report {
  text-align: center;
  padding: 40px 0;
}

/* 滚动条样式 */
.report-content::-webkit-scrollbar {
  width: 6px;
}

.report-content::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 3px;
}

.report-content::-webkit-scrollbar-thumb {
  background: var(--el-border-color-dark);
  border-radius: 3px;
}

.report-content::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-darker);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .report-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .report-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .report-content {
    max-height: 500px;
  }
  
  .markdown-content :deep(table) {
    font-size: 14px;
  }
  
  .markdown-content :deep(th),
  .markdown-content :deep(td) {
    padding: 8px 12px;
  }
}

/* 打印样式 */
@media print {
  .report-card {
    box-shadow: none;
    border: none;
  }
  
  .report-actions {
    display: none;
  }
  
  .report-content {
    max-height: none;
    overflow: visible;
  }
}
</style>