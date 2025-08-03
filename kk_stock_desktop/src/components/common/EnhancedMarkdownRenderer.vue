<template>
  <div class="enhanced-markdown-renderer">
    <div class="markdown-controls" v-if="showControls">
      <div class="controls-left">
        <button 
          @click="toggleTypewriter" 
          :class="['control-btn', isTyping ? 'active' : '']"
          :title="isTyping ? '暂停打字效果' : '开始打字效果'"
        >
          <PauseIcon v-if="isTyping" class="w-4 h-4" />
          <PlayIcon v-else class="w-4 h-4" />
        </button>
        
        <button 
          @click="resetTypewriter" 
          class="control-btn"
          title="重置打字效果"
        >
          <ArrowPathIcon class="w-4 h-4" />
        </button>
        
        <div class="speed-control">
          <label class="speed-label">速度:</label>
          <el-slider
            v-model="typingSpeed"
            :min="1"
            :max="10"
            :step="1"
            :show-tooltip="false"
            class="speed-slider"
            @input="updateTypingSpeed"
          />
        </div>
      </div>
      
      <div class="controls-right">
        <button 
          @click="exportMarkdown" 
          class="control-btn export-btn"
          title="导出Markdown"
        >
          <DocumentArrowDownIcon class="w-4 h-4" />
          导出MD
        </button>
        
        <button 
          @click="exportPDF" 
          class="control-btn export-btn"
          title="导出PDF"
        >
          <DocumentIcon class="w-4 h-4" />
          导出PDF
        </button>
      </div>
    </div>
    
    <div class="markdown-content" ref="contentContainer">
      <div 
        v-html="displayedContent" 
        class="markdown-body"
        ref="markdownContainer"
      ></div>
      
      <!-- 打字机光标 -->
      <div v-if="isTyping && showCursor" class="typing-cursor"></div>
      
      <!-- 进度指示器 -->
      <div v-if="showProgress && (isTyping || progress < 100)" class="progress-indicator">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
        <span class="progress-text">{{ Math.round(progress) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElSlider } from 'element-plus'
import { 
  PlayIcon, 
  PauseIcon, 
  ArrowPathIcon,
  DocumentArrowDownIcon,
  DocumentIcon
} from '@heroicons/vue/24/outline'
import { marked } from 'marked'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

interface Props {
  markdownText: string
  showControls?: boolean
  showProgress?: boolean
  showCursor?: boolean
  autoStart?: boolean
  typingSpeedInit?: number
  exportFileName?: string
}

const props = withDefaults(defineProps<Props>(), {
  showControls: true,
  showProgress: true,
  showCursor: true,
  autoStart: false,
  typingSpeedInit: 5,
  exportFileName: 'markdown-report'
})

const emit = defineEmits<{
  typingStart: []
  typingComplete: []
  typingPause: []
  exportStart: [type: 'md' | 'pdf']
  exportComplete: [type: 'md' | 'pdf']
}>()

// 响应式数据
const displayedContent = ref('')
const isTyping = ref(false)
const typingSpeed = ref(props.typingSpeedInit)
const currentIndex = ref(0)
const renderedMarkdown = ref('')

// DOM引用
const contentContainer = ref<HTMLElement>()
const markdownContainer = ref<HTMLElement>()

// 定时器
let typingTimer: number | null = null

// 计算属性
const progress = computed(() => {
  if (!renderedMarkdown.value) return 0
  return (currentIndex.value / renderedMarkdown.value.length) * 100
})

const typingDelay = computed(() => {
  // 速度1-10映射到100ms-10ms
  return 110 - (typingSpeed.value * 10)
})

// 方法
const renderMarkdown = () => {
  if (!props.markdownText) {
    renderedMarkdown.value = ''
    return
  }
  
  // 类型检查：确保markdownText是字符串类型
  let markdownContent = props.markdownText
  if (typeof markdownContent !== 'string') {
    console.warn('EnhancedMarkdownRenderer: markdownText应为字符串类型，收到:', typeof markdownContent, markdownContent)
    // 尝试转换为字符串
    if (markdownContent && typeof markdownContent === 'object') {
      markdownContent = JSON.stringify(markdownContent, null, 2)
    } else {
      markdownContent = String(markdownContent || '')
    }
  }
  
  // 配置marked选项
  marked.setOptions({
    breaks: true,
    gfm: true
  })
  
  renderedMarkdown.value = marked(markdownContent)
}

const startTypewriter = () => {
  if (isTyping.value || !renderedMarkdown.value) return
  
  isTyping.value = true
  emit('typingStart')
  
  const typeNextChar = () => {
    if (currentIndex.value < renderedMarkdown.value.length && isTyping.value) {
      currentIndex.value++
      displayedContent.value = renderedMarkdown.value.substring(0, currentIndex.value)
      
      // 自动滚动到底部
      nextTick(() => {
        if (contentContainer.value) {
          contentContainer.value.scrollTop = contentContainer.value.scrollHeight
        }
      })
      
      typingTimer = setTimeout(typeNextChar, typingDelay.value)
    } else {
      isTyping.value = false
      emit('typingComplete')
      
      if (typingTimer) {
        clearTimeout(typingTimer)
        typingTimer = null
      }
    }
  }
  
  typeNextChar()
}

const pauseTypewriter = () => {
  isTyping.value = false
  emit('typingPause')
  
  if (typingTimer) {
    clearTimeout(typingTimer)
    typingTimer = null
  }
}

const toggleTypewriter = () => {
  if (isTyping.value) {
    pauseTypewriter()
  } else {
    startTypewriter()
  }
}

const resetTypewriter = () => {
  pauseTypewriter()
  currentIndex.value = 0
  displayedContent.value = ''
  
  nextTick(() => {
    if (contentContainer.value) {
      contentContainer.value.scrollTop = 0
    }
  })
}

const updateTypingSpeed = () => {
  // 如果正在打字，重启定时器以应用新速度
  if (isTyping.value && typingTimer) {
    clearTimeout(typingTimer)
    startTypewriter()
  }
}

const exportMarkdown = async () => {
  try {
    emit('exportStart', 'md')
    
    const blob = new Blob([props.markdownText], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.exportFileName}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    emit('exportComplete', 'md')
    ElMessage.success('Markdown导出成功')
  } catch (error) {
    ElMessage.error('Markdown导出失败')
    console.error('Export markdown error:', error)
  }
}

const exportPDF = async () => {
  try {
    emit('exportStart', 'pdf')
    
    if (!markdownContainer.value) {
      throw new Error('Markdown容器未找到')
    }
    
    // 创建临时的全内容容器用于PDF导出
    const tempContainer = document.createElement('div')
    tempContainer.innerHTML = renderedMarkdown.value
    tempContainer.style.cssText = `
      position: absolute;
      top: -9999px;
      left: -9999px;
      width: 800px;
      padding: 40px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: #333;
      background: white;
    `
    
    // 添加CSS样式到临时容器
    const styles = document.createElement('style')
    styles.textContent = `
      h1, h2, h3, h4, h5, h6 { 
        margin-top: 24px; 
        margin-bottom: 12px; 
        color: #2c3e50; 
        font-weight: 600;
      }
      h1 { font-size: 24px; }
      h2 { font-size: 20px; }
      h3 { font-size: 18px; }
      table { 
        width: 100%; 
        border-collapse: collapse; 
        margin: 16px 0;
      }
      th, td { 
        border: 1px solid #ddd; 
        padding: 8px 12px; 
        text-align: left;
      }
      th { 
        background-color: #f8f9fa; 
        font-weight: 600;
      }
      p { margin: 12px 0; }
      ul, ol { margin: 12px 0; padding-left: 24px; }
      li { margin: 4px 0; }
      code { 
        background-color: #f5f5f5; 
        padding: 2px 4px; 
        border-radius: 3px;
        font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
      }
    `
    tempContainer.appendChild(styles)
    document.body.appendChild(tempContainer)
    
    const canvas = await html2canvas(tempContainer, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff'
    })
    
    document.body.removeChild(tempContainer)
    
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = pdfWidth - 20  // 10mm margin on each side
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    
    let yPosition = 10  // 10mm top margin
    let remainingHeight = imgHeight
    
    // 如果图片高度超过一页，分页处理
    while (remainingHeight > 0) {
      const pageHeight = Math.min(remainingHeight, pdfHeight - 20)  // 10mm margin top and bottom
      
      pdf.addImage(
        imgData, 
        'PNG', 
        10,  // 10mm left margin
        yPosition, 
        imgWidth, 
        pageHeight,
        undefined,
        'FAST'
      )
      
      remainingHeight -= pageHeight
      
      if (remainingHeight > 0) {
        pdf.addPage()
        yPosition = 10
      }
    }
    
    pdf.save(`${props.exportFileName}.pdf`)
    
    emit('exportComplete', 'pdf')
    ElMessage.success('PDF导出成功')
  } catch (error) {
    ElMessage.error('PDF导出失败')
    console.error('Export PDF error:', error)
  }
}

// 监听器
watch(() => props.markdownText, () => {
  renderMarkdown()
  resetTypewriter()
  
  if (props.autoStart && renderedMarkdown.value) {
    nextTick(() => {
      setTimeout(() => startTypewriter(), 500)
    })
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  renderMarkdown()
  
  if (props.autoStart && renderedMarkdown.value) {
    setTimeout(() => startTypewriter(), 1000)
  }
})

onUnmounted(() => {
  if (typingTimer) {
    clearTimeout(typingTimer)
  }
})

// 暴露方法给父组件
defineExpose({
  startTypewriter,
  pauseTypewriter,
  resetTypewriter,
  exportMarkdown,
  exportPDF
})
</script>

<style scoped>
.enhanced-markdown-renderer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.markdown-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-primary);
}

.controls-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-base);
}

.control-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border-accent);
  color: var(--text-primary);
}

.control-btn.active {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: white;
}

.export-btn {
  font-weight: 500;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.speed-label {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.speed-slider {
  width: 80px;
}

.markdown-content {
  flex: 1;
  overflow: auto;
  position: relative;
  padding: 0;
}

.markdown-body {
  padding: 24px;
  line-height: 1.6;
  color: var(--text-primary);
  max-width: none;
}

/* Markdown样式 */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 12px;
  color: var(--text-primary);
  font-weight: 600;
}

.markdown-body h1 {
  font-size: 28px;
  border-bottom: 2px solid var(--border-primary);
  padding-bottom: 8px;
}

.markdown-body h2 {
  font-size: 24px;
  border-bottom: 1px solid var(--border-secondary);
  padding-bottom: 6px;
}

.markdown-body h3 {
  font-size: 20px;
}

.markdown-body h4 {
  font-size: 18px;
}

.markdown-body p {
  margin: 12px 0;
}

.markdown-body ul,
.markdown-body ol {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-body li {
  margin: 4px 0;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid var(--border-primary);
  padding: 8px 12px;
  text-align: left;
}

.markdown-body th {
  background: var(--bg-tertiary);
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-body code {
  background: var(--bg-tertiary);
  color: var(--accent-primary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.9em;
}

.markdown-body pre {
  background: var(--bg-tertiary);
  padding: 16px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-body pre code {
  background: none;
  padding: 0;
  color: var(--text-primary);
}

.markdown-body blockquote {
  margin: 16px 0;
  padding: 12px 16px;
  background: var(--bg-elevated);
  border-left: 4px solid var(--accent-primary);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.markdown-body hr {
  border: none;
  border-top: 1px solid var(--border-primary);
  margin: 24px 0;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 20px;
  background: var(--accent-primary);
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.progress-indicator {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: var(--bg-elevated);
  border-top: 1px solid var(--border-primary);
  backdrop-filter: blur(10px);
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--border-secondary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent-primary);
  transition: width 0.2s ease;
  border-radius: 2px;
}

.progress-text {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 35px;
  text-align: right;
}

/* Element Plus样式覆盖 */
:deep(.el-slider__runway) {
  background-color: var(--border-secondary);
}

:deep(.el-slider__bar) {
  background-color: var(--accent-primary);
}

:deep(.el-slider__button) {
  border-color: var(--accent-primary);
  background-color: var(--accent-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .markdown-controls {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .controls-left,
  .controls-right {
    justify-content: center;
  }
  
  .speed-control {
    order: -1;
    justify-content: center;
  }
  
  .markdown-body {
    padding: 16px;
  }
  
  .markdown-body h1 {
    font-size: 24px;
  }
  
  .markdown-body h2 {
    font-size: 20px;
  }
}

/* 深色主题增强 */
.dark .control-btn.active {
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

.dark .typing-cursor {
  box-shadow: 0 0 8px var(--accent-primary);
}

.dark .progress-fill {
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
}
</style>