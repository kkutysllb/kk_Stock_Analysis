<template>
  <div class="ask-ai-component">
    <!-- AI问答按钮 -->
    <el-button 
      type="primary" 
      size="small" 
      @click="openAIDialog"
      :loading="loading"
      class="ask-ai-btn"
    >
      <el-icon class="ai-icon">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L13.09 8.26L16 7L14.74 10.09L21 12L14.74 13.91L16 17L13.09 15.74L12 22L10.91 15.74L8 17L9.26 13.91L3 12L9.26 10.09L8 7L10.91 8.26L12 2Z"/>
        </svg>
      </el-icon>
      问AI
    </el-button>

    <!-- AI侧边栏 -->
    <teleport to="body">
      <div v-show="dialogVisible" class="ai-sidebar-overlay" @click="handleClose">
        <div class="ai-sidebar-panel" @click.stop>
        <!-- 标题栏 -->
        <div class="ai-sidebar-header">
          <h3 class="ai-sidebar-title">AI数据分析助手</h3>
          <el-button 
            link 
            @click="handleClose"
            class="close-btn"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        
        <!-- 内容区域 -->
        <div class="ai-sidebar-content">
          <!-- 数据预览区域 -->
          <div class="data-preview-section">
            <h4>当前数据概览</h4>
            <div class="data-summary">
              <el-tag v-if="dataContext.type" type="info">{{ dataContext.type }}</el-tag>
              <el-tag v-if="dataContext.name" type="success">{{ dataContext.name }}</el-tag>
              <el-tag v-if="dataContext.period" type="warning">{{ dataContext.period }}</el-tag>
            </div>
            <div class="data-details" v-if="dataContext.summary">
              <p>{{ dataContext.summary }}</p>
            </div>
          </div>

          <!-- 对话历史 -->
          <div class="chat-history" ref="chatHistory">
            <div 
              v-for="(message, index) in chatMessages" 
              :key="index" 
              :class="['message', message.role]"
            >
              <div class="message-avatar">
                <el-icon v-if="message.role === 'user'"><User /></el-icon>
                <el-icon v-else><UserFilled /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text">
                  <span v-html="renderMarkdown(message.content, message.isStreaming)"></span>
                  <!-- 流式渲染时显示打字机光标效果 -->
                  <span v-if="message.isStreaming && isStreaming" class="typing-cursor">|</span>
                </div>
                
                <!-- 图表渲染区域 -->
                <div v-if="message.hasChart && message.chartConfig" class="chart-container">
                  <div class="chart-title">📊 数据可视化图表</div>
                  <VChart 
                    :option="message.chartConfig" 
                    :style="{ width: '100%', height: '400px' }"
                    :init-options="{ renderer: 'canvas' }"
                    :loading="false"
                    :loading-options="{ text: '图表加载中...' }"
                    autoresize
                    @error="handleChartError"
                  />
                </div>
                
                <div class="message-footer">
                  <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                  <!-- 重新回答按钮 - 只在AI消息且不在流式输出时显示 -->
                  <el-button 
                    v-if="message.role === 'assistant' && !message.isStreaming && message.originalQuestion"
                    class="regenerate-btn"
                    size="small"
                    type="info"
                    plain
                    :loading="loading"
                    @click="regenerateAnswer(message.originalQuestion!)"
                    title="重新回答这个问题"
                  >
                    <el-icon><Refresh /></el-icon>
                    重新回答
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-section">
            <el-input
              v-model="userInput"
              type="textarea"
              :rows="3"
              placeholder="请输入您想了解的问题，比如：分析一下这个数据的趋势如何？"
              @keydown.ctrl.enter="sendMessage"
              @keydown.esc="isStreaming ? stopStreaming() : null"
              :disabled="loading"
            />
            <div class="input-actions">
              <div class="quick-questions">
                <el-button 
                  v-for="question in quickQuestions" 
                  :key="question"
                  size="small" 
                  type="info" 
                  plain
                  @click="selectQuickQuestion(question)"
                  :disabled="loading"
                >
                  {{ question }}
                </el-button>
              </div>
              <div class="send-actions">
                <span class="tip">{{ isStreaming ? 'Esc 停止' : 'Ctrl + Enter 发送' }}</span>
                <el-button 
                  :type="isStreaming ? 'danger' : 'primary'"
                  @click="isStreaming ? stopStreaming() : sendMessage()"
                  :loading="loading && !isStreaming"
                  :disabled="!isStreaming && !userInput.trim()"
                >
                  {{ isStreaming ? '停止输出' : '发送' }}
                </el-button>
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch, getCurrentInstance } from 'vue'
import { 
  ElButton, 
  ElDialog, 
  ElInput, 
  ElTag, 
  ElIcon,
  ElMessage
} from 'element-plus'
import { 
  ChatDotRound, 
  User, 
  UserFilled,
  Close,
  Refresh
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import * as echarts from 'echarts'
import VChart from 'vue-echarts'
import { getAIMessages, getCurrentSystemPrompt } from '@/utils/aiPromptManager'

// 注册VChart组件
const components = {
  VChart
}
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/tag/style/css'
import 'element-plus/es/components/icon/style/css'
import 'element-plus/es/components/message/style/css'

// 定义props
interface Props {
  // 数据上下文
  dataContext: {
    type?: string // 数据类型，如"指数数据"、"ETF数据"等
    name?: string // 数据名称，如"上证指数"、"沪深300ETF"等
    period?: string // 时间周期，如"日线"、"周线"等
    data?: any // 实际数据
    summary?: string // 数据摘要
  }
}

const props = defineProps<Props>()

// 为 props 提供默认值
const dataContext = computed(() => props.dataContext || {})

// 响应式数据
const dialogVisible = ref(false)
const loading = ref(false)
const userInput = ref('')
const chatHistory = ref<HTMLElement | null>(null)
const isStreaming = ref(false)
let abortController: AbortController | null = null

// 聊天消息接口
interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  hasChart?: boolean
  chartConfig?: any
  originalQuestion?: string // 存储AI回答对应的原始用户问题
}

const chatMessages = ref<Message[]>([])

// 快速问题模板
const quickQuestions = [
  '分析一下当前数据的趋势',
  '这个数据表现如何？',
  '有什么投资建议吗？',
  '风险点在哪里？',
  '生成一个示例图表展示数据'
]

// 流式滚动节流控制
let scrollThrottle: ReturnType<typeof setTimeout> | null = null

const throttledScrollToBottom = () => {
  if (scrollThrottle) {
    clearTimeout(scrollThrottle)
  }
  
  // 根据模型类型调整节流时间 - 在线模型使用更长的节流时间以改善流式效果
  const throttleTime = aiConfig.value.modelType === 'online' ? 100 : 50
  
  scrollThrottle = setTimeout(() => {
    scrollToBottom()
    scrollThrottle = null
  }, throttleTime)
}

// AI配置管理
const aiConfig = ref({
  modelType: 'online',
  onlineProvider: 'deepseek',
  onlineApiUrl: 'https://api.deepseek.com/v1/chat/completions',
  onlineApiKey: 'sk-67e4607685404186a881325dab701fb4',
  onlineModelName: 'deepseek-reasoner',
  localServiceType: 'ollama',
  localApiUrl: 'http://localhost:11434/v1/chat/completions',
  localModelName: 'qwen3:32b',
  localApiKey: '',
  maxTokens: 2000,
  temperature: 0.7,
  timeout: 60,
  enableAnalysis: true, // 智能分析开关
  enableStreaming: true // 流式输出开关 - 确保在线模型和本地模型都默认启用
})

// 从本地存储加载AI配置
const loadAIConfig = () => {
  try {
    const savedConfig = localStorage.getItem('kk-stock-ai-config')
    if (savedConfig) {
      const parsedConfig = JSON.parse(savedConfig)
      Object.assign(aiConfig.value, parsedConfig)
  
    } else {

    }
  } catch (error) {

    ElMessage.error('加载AI配置失败，请检查设置')
  }
}

// 监听配置更新事件
const handleConfigUpdate = (event: Event) => {
  const customEvent = event as CustomEvent

  loadAIConfig()
  ElMessage.success('AI配置已更新')
}

// 打开AI对话框
const openAIDialog = () => {
  // 重新加载最新配置
  loadAIConfig()
  
  // 检查AI智能分析是否启用
  if (!aiConfig.value.enableAnalysis) {
    ElMessage.warning('AI智能分析不可用，请在设置中启用后再试')
    return
  }
  
  // 检查基本配置是否完整
  const apiUrl = aiConfig.value.modelType === 'online' 
    ? aiConfig.value.onlineApiUrl 
    : aiConfig.value.localApiUrl
  
  if (!apiUrl) {
    ElMessage.error('AI服务配置不完整，请在设置中配置API地址')
    return
  }
  
  dialogVisible.value = true
  
  // 如果是首次打开，添加欢迎消息
  if (chatMessages.value.length === 0) {
    const modelTypeText = aiConfig.value.modelType === 'online' ? '在线模型' : '本地模型'
    const streamingText = aiConfig.value.enableStreaming ? '已启用实时流式输出' : '已禁用流式输出'
    const contextName = dataContext.value.name || dataContext.value.type || '数据'
    
    chatMessages.value.push({
      role: 'assistant',
      content: `您好！我是AI数据分析助手。

📊 **当前分析对象：${contextName}**

系统信息：使用${modelTypeText}，${streamingText}

我已经获取到您当前查看的${contextName}的完整数据信息，包括价格走势、成交量、涨跌幅等关键指标。请问您想了解什么？

💡 **建议提问：**
- 分析一下${contextName}的趋势如何？
- 这个数据表现如何？有什么特点？
- 给出投资建议和风险提示
- 与其他标的进行对比分析`,
      timestamp: new Date()
    })
  }
}

// 关闭对话框
const handleClose = () => {
  // 如果正在流式输出，先停止
  if (isStreaming.value) {
    stopStreaming()
  }
  dialogVisible.value = false
}

// 选择快速问题
const selectQuickQuestion = (question: string) => {
  userInput.value = question
}

// 停止流式输出
const stopStreaming = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  isStreaming.value = false
  loading.value = false
  
  // 如果有正在流式输出的消息，标记为完成
  const lastMessage = chatMessages.value[chatMessages.value.length - 1]
  if (lastMessage && lastMessage.isStreaming) {
    lastMessage.isStreaming = false
    if (!lastMessage.content.trim()) {
      lastMessage.content = '[输出已停止]'
    }
  }
  
  
}

// 重新回答问题
const regenerateAnswer = async (originalQuestion: string) => {
  if (!originalQuestion || loading.value || isStreaming.value) return

  // 检查AI智能分析是否启用
  if (!aiConfig.value.enableAnalysis) {
    ElMessage.warning('AI智能分析功能已关闭，请在设置中启用后再试')
    return
  }


  
  // 添加用户消息（重新提问）
  chatMessages.value.push({
    role: 'user',
    content: originalQuestion,
    timestamp: new Date()
  })

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 调用AI API
  await callAIAPI(originalQuestion)
}

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  // 检查AI智能分析是否启用
  if (!aiConfig.value.enableAnalysis) {
    ElMessage.warning('AI智能分析功能已关闭，请在设置中启用后再试')
    return
  }

  const userMessage = userInput.value.trim()
  userInput.value = ''

  // 添加用户消息
  chatMessages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 调用AI API
  await callAIAPI(userMessage)
}

// 调用AI API（支持在线和本地模型）
const callAIAPI = async (userMessage: string) => {
  loading.value = true
  isStreaming.value = true
  
  // 创建新的AbortController用于中断请求
  abortController = new AbortController()
  
  // 根据配置选择API地址、密钥和模型
  const apiUrl = aiConfig.value.modelType === 'online' 
    ? aiConfig.value.onlineApiUrl 
    : aiConfig.value.localApiUrl
  
  const apiKey = aiConfig.value.modelType === 'online' 
    ? aiConfig.value.onlineApiKey 
    : aiConfig.value.localApiKey
  
  const modelName = aiConfig.value.modelType === 'online' 
    ? aiConfig.value.onlineModelName 
    : aiConfig.value.localModelName
  
  try {
    // 使用自适应提示词管理系统构建消息
    const context = dataContext.value
    const contextName = context.name || context.type || '数据'
    
    // 在用户消息前添加明确的数据上下文说明
    const contextualUserMessage = `[当前分析对象: ${contextName}]

${userMessage}

请基于我当前查看的${contextName}数据进行分析回答。`
    
    const baseMessages = getAIMessages(contextualUserMessage, {
      dataType: context.type,
      dataName: context.name,
      period: context.period,
      summary: context.summary,
      data: context.data
    })
    
    // 构建消息历史 - 限制消息数量以避免超出token限制
    // 对于本地模型，使用更少的历史消息以节省token
    const maxHistoryMessages = aiConfig.value.modelType === 'local' ? 5 : 8
    const messages = [
      baseMessages[0], // 系统提示词
      ...chatMessages.value.slice(-maxHistoryMessages).map(msg => ({
        role: msg.role,
        content: msg.content.length > 1000 ? msg.content.substring(0, 1000) + '...' : msg.content
      })),
      baseMessages[1] // 当前用户消息
    ]

    // 创建一个空的AI消息用于流式更新
    const aiMessageIndex = chatMessages.value.length
    chatMessages.value.push({
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      originalQuestion: userMessage // 存储原始用户问题
    })
    
    // 构建请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    
    // 只有在线模型或本地模型有API密钥时才添加Authorization头
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`
    }
    
    // 对于在线模型，添加防缓存头以确保流式数据实时传输
    if (aiConfig.value.modelType === 'online') {
      headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
      headers['Pragma'] = 'no-cache'
      headers['Expires'] = '0'
      
    }

    // 检查是否为Ollama服务
    const isOllama = aiConfig.value.modelType === 'local' && aiConfig.value.localServiceType === 'ollama'
    
    // 为Ollama服务调整API地址
    let finalApiUrl = apiUrl
    if (isOllama && apiUrl.includes('/v1/chat/completions')) {
      finalApiUrl = apiUrl.replace('/v1/chat/completions', '/api/generate')
      
    }
    
    // 构建请求体 - 根据服务类型使用不同格式
    let requestBody: any
    
    if (isOllama) {
      // Ollama原生格式
      const systemPrompt = messages.find(msg => msg.role === 'system')?.content || ''
      const userMessages = messages.filter(msg => msg.role !== 'system')
      const conversationHistory = userMessages.map(msg => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`).join('\n')
      
      requestBody = {
        model: modelName,
        prompt: systemPrompt + '\n\n' + conversationHistory,
        stream: aiConfig.value.enableStreaming !== false,
        options: {
          temperature: aiConfig.value.temperature,
          num_predict: aiConfig.value.maxTokens
        }
      }
    } else {
      // 标准OpenAI格式
      requestBody = {
        model: modelName,
        messages: messages,
        temperature: aiConfig.value.temperature,
        max_tokens: aiConfig.value.maxTokens,
        // 根据模型类型和配置决定是否启用流式输出
        stream: aiConfig.value.enableStreaming !== false // 默认启用，除非明确禁用
      }
      
      // 对于某些在线服务，可能需要额外的流式配置
      if (aiConfig.value.modelType === 'online' && requestBody.stream) {
        // 添加流式输出优化参数
        requestBody.stream_options = {
          include_usage: false // 减少响应数据量
        }
        // 确保在线模型强制启用流式输出
      }
    }
    


    const response = await fetch(finalApiUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody),
      signal: abortController.signal
    })

    if (!response.ok) {
      // 获取详细的错误信息
      let errorDetails = ''
      try {
        const errorText = await response.text()
        errorDetails = errorText

      } catch (e) {

      }
      
      throw new Error(`API请求失败: ${response.status} ${response.statusText}${errorDetails ? '\n错误详情: ' + errorDetails : ''}`)
    }

    // 处理响应（支持流式和非流式）
    let fullContent = ''
    
    if (requestBody.stream) {
      // 流式响应处理
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        let buffer = ''
        let chunkCount = 0
        let firstChunkReceived = false
        
  
        
        // 特别针对在线模型的流式处理优化
        if (aiConfig.value.modelType === 'online') {
  
        }
        
        while (true) {
          // 检查是否需要中断
          if (abortController?.signal.aborted) {
            break
          }
          
          const { done, value } = await reader.read()
          if (done) {
            break
          }

          const chunk = decoder.decode(value, { stream: true })
          buffer += chunk
          chunkCount++
          

          
          // 按行分割处理
          const lines = buffer.split('\n')
          // 保留最后一行（可能不完整）
          buffer = lines.pop() || ''

          for (const line of lines) {
            const trimmedLine = line.trim()
            if (!trimmedLine) continue
            
            let jsonData = null
            
            // 处理标准SSE格式 (data: {...})
            if (trimmedLine.startsWith('data: ')) {
              const data = trimmedLine.slice(6)
              if (data === '[DONE]') {
                break
              }
              try {
                jsonData = JSON.parse(data)
              } catch (e: any) {
                continue
              }
            }
            // 处理直接JSON格式 ({...})
            else if (trimmedLine.startsWith('{') && trimmedLine.endsWith('}')) {
              try {
                jsonData = JSON.parse(trimmedLine)
              } catch (e: any) {
                // 忽略解析错误，继续处理下一行
                continue
              }
            }
            
            // 提取内容
            if (jsonData) {
              let content = ''
              
              if (isOllama) {
                // Ollama原生格式处理
                if (jsonData.response) {
                  content = jsonData.response
                } else if (jsonData.message && jsonData.message.content) {
                  content = jsonData.message.content
                } else if (jsonData.content) {
                  content = jsonData.content
                }
              } else {
                // 标准OpenAI格式
                if (jsonData.choices && jsonData.choices[0] && jsonData.choices[0].delta) {
                  const delta = jsonData.choices[0].delta

                  
                  // 尝试多种可能的内容字段
                  if (delta.content) {
                    content = delta.content
                  } else if (delta.text) {
                    content = delta.text
                  } else if (delta.message && delta.message.content) {
                    content = delta.message.content
                  } else if (delta.message && typeof delta.message === 'string') {
                    content = delta.message
                  } else if (delta.response) {
                    content = delta.response
                  } else if (delta.data) {
                    content = delta.data
                  } else if (delta.output) {
                    content = delta.output
                  } else {
                    // 如果没有找到标准字段，尝试第一个字符串值
                    for (const [key, value] of Object.entries(delta)) {
                      if (typeof value === 'string' && value.trim() && key !== 'role' && key !== 'finish_reason') {
                        content = value

                        break
                      }
                    }
                  }
                }
                // 其他可能的格式
                else if (jsonData.content) {
                  content = jsonData.content
                }
                else if (jsonData.text) {
                  content = jsonData.text
                }
                else if (jsonData.response) {
                  content = jsonData.response
                }
              }
            
              if (content) {
                fullContent += content
                
                // 特别处理在线模型的第一个数据块
                if (aiConfig.value.modelType === 'online' && !firstChunkReceived) {
                  firstChunkReceived = true
                }
                
                // 立即更新消息内容 - 确保在线模型和本地模型都能实时渲染
                // 流式输出时只渲染markdown和表格，不处理图表
                chatMessages.value[aiMessageIndex].content = fullContent
                
                // 强制触发Vue的响应式更新和DOM重新渲染
                nextTick(() => {
                  // 强制组件更新以确保流式效果可见
                  if (getCurrentInstance()) {
                    getCurrentInstance()?.proxy?.$forceUpdate()
                  }
                  // 实时滚动到底部
                  throttledScrollToBottom()
                })
                
                // 添加调试信息，确保在线模型也能实时更新
                if (aiConfig.value.modelType === 'online' && chunkCount % 8 === 0) {
  
                }
              }
            }
          }
        }
        
        // 处理缓冲区中剩余的数据
        if (buffer.trim()) {
          const trimmedBuffer = buffer.trim()
          if (trimmedBuffer.startsWith('{') && trimmedBuffer.endsWith('}')) {
            try {
              const jsonData = JSON.parse(trimmedBuffer)
              let content = ''
              
              if (isOllama) {
                // Ollama原生格式处理
                if (jsonData.response) {
                  content = jsonData.response
                } else if (jsonData.message && jsonData.message.content) {
                  content = jsonData.message.content
                } else if (jsonData.content) {
                  content = jsonData.content
                }
              } else {
                // 标准OpenAI格式
                if (jsonData.choices && jsonData.choices[0] && jsonData.choices[0].delta && jsonData.choices[0].delta.content) {
                  content = jsonData.choices[0].delta.content
                } else if (jsonData.content) {
                  content = jsonData.content
                } else if (jsonData.text) {
                  content = jsonData.text
                } else if (jsonData.response) {
                  content = jsonData.response
                }
              }
              
              if (content) {
                fullContent += content
                
                // 立即更新消息内容 - 确保缓冲区内容也能实时渲染
                // 流式输出时只渲染markdown和表格，不处理图表
                chatMessages.value[aiMessageIndex].content = fullContent
                
                // 强制触发Vue的响应式更新
                nextTick(() => {
                  // 实时滚动到底部
                  throttledScrollToBottom()
                })
                
                // 添加调试信息

              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } else {
      // 非流式响应处理
      const responseData = await response.json()
      
      if (isOllama) {
        // Ollama格式处理
        if (responseData.response) {
          fullContent = responseData.response
        } else if (responseData.message && responseData.message.content) {
          fullContent = responseData.message.content
        } else if (responseData.content) {
          fullContent = responseData.content
        }
      } else {
        // 标准OpenAI格式
        if (responseData.choices && responseData.choices[0] && responseData.choices[0].message) {
          fullContent = responseData.choices[0].message.content
        }
      }
      
      if (fullContent) {
        // 更新消息内容
        chatMessages.value[aiMessageIndex].content = fullContent
        
        // 检测和渲染图表
        const chartResult = detectAndParseChart(fullContent)
        if (chartResult.hasChart) {
  
          chatMessages.value[aiMessageIndex].hasChart = true
          chatMessages.value[aiMessageIndex].chartConfig = chartResult.chartConfig
          chatMessages.value[aiMessageIndex].content = chartResult.cleanContent
        }
        
        // 滚动到底部
        await nextTick()
        scrollToBottom()
      }
    }

    // 完成流式输出
    chatMessages.value[aiMessageIndex].isStreaming = false
    
    // 流式结束后，统一检测和渲染图表
    if (fullContent) {
      const chartResult = detectAndParseChart(fullContent)
      if (chartResult.hasChart) {

        chatMessages.value[aiMessageIndex].hasChart = true
        chatMessages.value[aiMessageIndex].chartConfig = chartResult.chartConfig
        chatMessages.value[aiMessageIndex].content = chartResult.cleanContent
        
        // 图表渲染后滚动到底部
        await nextTick()
        scrollToBottom()
      }
    }

  } catch (error) {

    
    // 检查是否是用户主动中断
    if (error instanceof Error && error.name === 'AbortError') {

      // 不显示错误消息，因为这是用户主动操作
      return
    }
    
    // 提供更具体的错误信息
    let errorMessage = 'AI服务暂时不可用'
    let detailMessage = '抱歉，我暂时无法回答您的问题，请稍后重试。'
    
    if (error instanceof Error) {
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage = '网络连接失败，请检查AI服务地址是否正确'
        detailMessage = `无法连接到AI服务 (${apiUrl})，请检查：\n1. 服务地址是否正确\n2. 网络连接是否正常\n3. AI服务是否已启动`
      } else if (error.message.includes('401')) {
        errorMessage = 'API密钥验证失败'
        detailMessage = 'API密钥无效或已过期，请在设置中检查API密钥配置'
      } else if (error.message.includes('400')) {
        errorMessage = 'API请求参数错误'
        detailMessage = `请求参数格式错误，可能的原因：\n1. 模型名称不正确（当前: ${modelName}）\n2. 本地服务不支持某些参数（如stream）\n3. 请检查API服务是否支持当前模型\n4. 详细错误: ${error.message}`
      } else if (error.message.includes('404')) {
        errorMessage = 'API接口不存在'
        detailMessage = 'API地址或模型名称配置错误，请检查设置中的配置信息'
      } else if (error.message.includes('timeout')) {
        errorMessage = '请求超时'
        detailMessage = 'AI服务响应超时，请稍后重试或检查网络连接'
      } else {
        detailMessage = `连接错误: ${error.message}`
      }
    }
    
    ElMessage.error(errorMessage)
    
    // 添加错误消息
    chatMessages.value.push({
      role: 'assistant',
      content: detailMessage,
      timestamp: new Date()
    })
  } finally {
    loading.value = false
    isStreaming.value = false
    abortController = null
    
    // 确保最后一条消息不再处于流式状态
    const lastMessage = chatMessages.value[chatMessages.value.length - 1]
    if (lastMessage && lastMessage.isStreaming) {
      lastMessage.isStreaming = false
    }
  }
}

// 构建系统提示词
const buildSystemPrompt = () => {
  const context = dataContext.value
  
  // 使用自适应提示词管理系统
  return getCurrentSystemPrompt({
    dataType: context.type,
    dataName: context.name,
    period: context.period,
    summary: context.summary,
    data: context.data
  })
}

// 验证图表配置
const validateChartConfig = (config: any): any => {
  try {
    // 深度克隆配置以避免修改原始数据
    const validatedConfig = JSON.parse(JSON.stringify(config))
    
    // 递归清理配置中的无效数据
    const cleanConfig = (obj: any): any => {
      if (typeof obj !== 'object' || obj === null) {
        return obj
      }
      
      if (Array.isArray(obj)) {
        return obj.map(item => cleanConfig(item))
      }
      
      const cleaned: any = {}
      for (const [key, value] of Object.entries(obj)) {
        // 跳过函数类型的值
        if (typeof value === 'function') {
          continue
        }
        
        // 确保对象属性不是字符串（除非是预期的字符串属性）
        if (typeof value === 'string') {
          // 允许的字符串属性
          const allowedStringProps = [
            'type', 'name', 'text', 'subtext', 'orient', 'align', 
            'verticalAlign', 'color', 'backgroundColor', 'borderColor',
            'fontFamily', 'fontSize', 'fontWeight', 'fontStyle',
            'formatter', 'unit', 'position', 'trigger', 'axisType',
            'coordinateSystem', 'symbol', 'symbolSize', 'lineStyle',
            'itemStyle', 'label', 'emphasis', 'select', 'blur'
          ]
          
          // 如果是数据数组中的字符串，也允许
          if (key === 'data' || allowedStringProps.includes(key) || 
              key.includes('Color') || key.includes('Style') || 
              key.includes('Format')) {
            cleaned[key] = value
          } else {
            // 对于不应该是字符串的属性，尝试解析为数字或跳过
            const numValue = parseFloat(value)
            if (!isNaN(numValue)) {
              cleaned[key] = numValue
            }
            // 否则跳过这个属性
          }
        } else {
          cleaned[key] = cleanConfig(value)
        }
      }
      return cleaned
    }
    
    const cleanedConfig = cleanConfig(validatedConfig)
    
    // 基本结构验证
    if (!cleanedConfig || typeof cleanedConfig !== 'object') {
      
      return null
    }
    
    // 确保有基本的图表结构
    if (!cleanedConfig.series && !cleanedConfig.dataset) {
      
      return null
    }
    
    return cleanedConfig
  } catch (error) {
    
    return null
  }
}

// 检测和解析图表代码
const detectAndParseChart = (content: string) => {
  // 匹配各种图表代码块格式
  const chartPatterns = [
    // ECharts配置对象 - 更宽松的匹配
    /```(?:javascript|js|echarts)?\s*\n[\s\S]*?option\s*=\s*(\{[\s\S]*?\})\s*[\s\S]*?\n```/gi,
    // JSON格式的ECharts配置 - 匹配包含series的JSON
    /```(?:json|echarts)?\s*\n(\{[\s\S]*?"series"[\s\S]*?\})\s*\n```/gi,
    // 简单的JSON对象格式
    /```(?:json)?\s*\n(\{[\s\S]*?"type"[\s\S]*?\})\s*\n```/gi,
    // Mermaid图表
    /```mermaid\s*\n([\s\S]*?)\n```/gi,
    // 表格格式
    /```(?:table|csv)?\s*\n([\s\S]*?)\n```/gi
  ]

  for (const pattern of chartPatterns) {
    const matches = content.match(pattern)
    if (matches) {
      for (const match of matches) {
        try {
          const code = match.replace(/```[\w]*\s*\n?|```/g, '').trim()
          
          // 检查是否是Mermaid图表
          if (match.includes('mermaid')) {
      
            // 这里可以添加Mermaid图表的处理逻辑
            // 暂时跳过Mermaid图表的处理
            continue
          }
          
          // 尝试解析ECharts配置
          let chartConfig = null
          
          if (code.includes('option') && code.includes('{')) {
            // 提取option对象
            const optionMatch = code.match(/option\s*=\s*(\{[\s\S]*\})/)
            if (optionMatch) {
              try {
                // 安全地评估JavaScript对象
                chartConfig = new Function('return ' + optionMatch[1])()
              } catch (e) {
        
              }
            }
          } else if (code.startsWith('{') && (code.includes('"series"') || code.includes('"type"'))) {
            // 直接JSON格式
            try {
              chartConfig = JSON.parse(code)
            } catch (e) {
      
              // 尝试修复常见的JSON格式问题
              try {
                const fixedCode = code
                  .replace(/([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:/g, '$1"$2":') // 添加缺失的引号
                  .replace(/'/g, '"') // 单引号转双引号
                chartConfig = JSON.parse(fixedCode)
              } catch (e2) {
      
              }
            }
          }
          
          if (chartConfig) {
            // 验证和清理图表配置
            const validatedConfig = validateChartConfig(chartConfig)
            if (validatedConfig) {

              return {
                hasChart: true,
                chartConfig: validatedConfig,
                cleanContent: content.replace(match, '\n\n*[图表已渲染]*\n\n')
              }
            }
          }
        } catch (error) {

        }
      }
    }
  }
  
  return { hasChart: false, chartConfig: null, cleanContent: content }
}

// 缓存已处理的思考块，避免重复处理
const processedThinkingBlocks = new Map<string, string>()

// 渲染Markdown内容
const renderMarkdown = (content: string, isStreaming = false) => {
  try {
    // 配置marked选项
    marked.use({
      breaks: true, // 支持换行
      gfm: true // 支持GitHub风格的Markdown
    })
    
    // 处理思考部分 <think></think>
    const processThinkingContent = (text: string) => {
      // 匹配所有的思考标签
      const thinkRegex = /<think>([\s\S]*?)<\/think>/gi
      
      return text.replace(thinkRegex, (match, thinkContent) => {
        // 使用内容作为缓存key
        const cacheKey = thinkContent.trim()
        
        // 检查缓存
        if (processedThinkingBlocks.has(cacheKey)) {
          return processedThinkingBlocks.get(cacheKey)!
        }
        
        // 渲染思考部分的markdown
        const renderedThinkContent = marked.parse(thinkContent.trim())
        
        // 包装在特殊的思考样式div中
        const result = `<div class="ai-thinking-block">
          <div class="thinking-header">
            <svg class="thinking-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <span class="thinking-label">AI思考过程</span>
          </div>
          <div class="thinking-content">${renderedThinkContent}</div>
        </div>`
        
        // 缓存结果
        processedThinkingBlocks.set(cacheKey, result)
        return result
      })
    }
    
    // 如果是流式输出，隐藏图表代码块，显示占位符
    const hideChartsInStreaming = (text: string) => {
      if (!isStreaming) return text
      
      // 匹配各种图表代码块格式
      const chartPatterns = [
        /```(?:javascript|js|echarts)?\s*\n[\s\S]*?option\s*=\s*\{[\s\S]*?\}\s*[\s\S]*?\n```/gi,
        /```(?:json|echarts)?\s*\n\{[\s\S]*?"series"[\s\S]*?\}\s*\n```/gi,
        /```(?:json)?\s*\n\{[\s\S]*?"type"[\s\S]*?\}\s*\n```/gi,
        /```mermaid\s*\n[\s\S]*?\n```/gi
      ]
      
      let processedText = text
      for (const pattern of chartPatterns) {
        processedText = processedText.replace(pattern, () => {
          return `<div class="chart-placeholder">
            <div class="placeholder-content">
              📊 <span class="loading-dots">图表生成中</span>
            </div>
          </div>`
        })
      }
      
      return processedText
    }
    
    // 先处理思考标签
    let processedContent = processThinkingContent(content)
    
    // 如果是流式输出，隐藏图表
    processedContent = hideChartsInStreaming(processedContent)
    
    // 对非思考部分进行markdown渲染
    const parts = processedContent.split(/(<div class="ai-thinking-block">[\s\S]*?<\/div>)/g)
    const finalContent = parts.map(part => {
      if (part.startsWith('<div class="ai-thinking-block">')) {
        // 思考部分已经处理过了，直接返回
        return part
      } else {
        // 非思考部分进行markdown渲染
        return part ? marked.parse(part) : ''
      }
    }).join('')
    
    return finalContent
  } catch (error) {
    // 如果渲染失败，返回原始内容
    return content.replace(/\n/g, '<br>')
  }
}

// 格式化时间
const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理图表渲染错误
const handleChartError = (error: any) => {

  ElMessage.warning('图表渲染失败，请检查数据格式')
}

// 滚动到底部
const scrollToBottom = () => {
  if (chatHistory.value) {
    chatHistory.value.scrollTop = chatHistory.value.scrollHeight
  }
}

// 监听数据上下文变化，自动清空历史消息
const lastDataContext = ref<string>('')

// 生成数据上下文的唯一标识
const getDataContextKey = (context: any) => {
  if (!context) return ''
  return `${context.type || ''}-${context.name || ''}-${context.period || ''}-${JSON.stringify(context.data?.selectedIndex || context.data?.selectedETF || context.data?.selectedSwanIndex || '')}`
}

// 监听数据上下文变化
watch(
  () => dataContext.value,
  (newContext: any, oldContext: any) => {
    const newKey = getDataContextKey(newContext)
    const oldKey = lastDataContext.value
    
    // 如果数据上下文发生了实质性变化
    if (newKey && oldKey && newKey !== oldKey) {

      
      // 清空聊天历史
      chatMessages.value = []
      
      // 清空思考块缓存
      processedThinkingBlocks.clear()
      
      // 添加数据变更提示消息
      const context = newContext || {}
      const contextName = context.name || context.type || '数据'
      chatMessages.value.push({
        role: 'assistant',
        content: `📊 **数据已切换** 

我注意到您切换到了新的分析对象：**${contextName}**

之前的对话历史已清空，现在我将基于当前的${contextName}数据为您提供分析。请问您想了解什么？

💡 **快速开始：**
- 分析当前数据的趋势
- 评估投资风险和机会  
- 与其他标的进行对比
- 获取具体的投资建议`,
        timestamp: new Date()
      })
      
      // 滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
    }
    
    // 更新上次的数据上下文标识
    lastDataContext.value = newKey
  },
  { deep: true, immediate: true }
)

// 组件挂载时的初始化
onMounted(() => {
  // 加载AI配置
  loadAIConfig()
  
  // 监听来自Settings页面的配置更新事件
  window.addEventListener('ai-config-updated', handleConfigUpdate)
})

// 组件卸载时清理事件监听器
onUnmounted(() => {
  window.removeEventListener('ai-config-updated', handleConfigUpdate)
  // 清理滚动节流定时器
  if (scrollThrottle) {
    clearTimeout(scrollThrottle)
  }
  // 清理AbortController
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  // 重置状态
  isStreaming.value = false
  loading.value = false
})
</script>

<style scoped>
.ask-ai-btn {
  --el-button-size: 32px;
  --el-button-padding: 8px 16px;
  font-size: 14px;
  font-weight: 700;
  border-radius: 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  border: 3px solid rgba(255, 255, 255, 0.3);
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  box-shadow: 
    0 6px 20px rgba(102, 126, 234, 0.5),
    inset 0 2px 0 rgba(255, 255, 255, 0.3),
    inset 0 -2px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

/* 添加闪光效果 */
.ask-ai-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.6s ease-in-out;
}

.ask-ai-btn:hover::before {
  left: 100%;
}

/* 添加彩虹边框效果 */
.ask-ai-btn::after {
  content: '';
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57, #ff9ff3, #54a0ff);
  background-size: 400% 400%;
  border-radius: 28px;
  z-index: -1;
  opacity: 0;
  animation: rainbow 3s ease infinite;
  transition: opacity 0.3s ease;
}

.ask-ai-btn:hover::after {
  opacity: 0.8;
}

@keyframes rainbow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.ask-ai-btn:hover {
  transform: translateY(-3px) scale(1.08) rotate(1deg);
  box-shadow: 
    0 12px 35px rgba(102, 126, 234, 0.7),
    inset 0 2px 0 rgba(255, 255, 255, 0.4),
    inset 0 -2px 0 rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.ask-ai-btn:active {
  transform: translateY(-1px) scale(1.05) rotate(0deg);
  transition: all 0.1s ease;
}

.ask-ai-btn .btn-icon {
  font-size: 18px;
  margin-right: 6px;
  animation: robotBounce 2s infinite ease-in-out;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

.ask-ai-btn .ai-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  animation: sparkle 2s ease-in-out infinite;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

@keyframes sparkle {
  0%, 100% { 
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
  50% { 
    transform: scale(1.1) rotate(180deg);
    opacity: 0.8;
  }
}

/* 更可爱的机器人弹跳动画 */
@keyframes robotBounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  10% {
    transform: translateY(-2px) rotate(-5deg);
  }
  30% {
    transform: translateY(-4px) rotate(5deg);
  }
  40% {
    transform: translateY(-3px) rotate(-3deg);
  }
  60% {
    transform: translateY(-2px) rotate(3deg);
  }
  70% {
    transform: translateY(-1px) rotate(-1deg);
  }
}

/* 添加脉冲效果 */
.ask-ai-btn:not(:hover) {
  animation: pulse 3s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 
      0 6px 20px rgba(102, 126, 234, 0.5),
      inset 0 2px 0 rgba(255, 255, 255, 0.3),
      inset 0 -2px 0 rgba(0, 0, 0, 0.1);
  }
  50% {
    box-shadow: 
      0 6px 20px rgba(102, 126, 234, 0.7),
      inset 0 2px 0 rgba(255, 255, 255, 0.3),
      inset 0 -2px 0 rgba(0, 0, 0, 0.1);
  }
  100% {
    box-shadow: 
      0 6px 20px rgba(102, 126, 234, 0.5),
      inset 0 2px 0 rgba(255, 255, 255, 0.3),
      inset 0 -2px 0 rgba(0, 0, 0, 0.1);
  }
}

/* 图表容器优化 - 减少渲染抖动 */
.chart-container {
  min-height: 400px;
  margin: 16px 0;
  padding: 16px;
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease-in-out;
  will-change: height;
  /* 减少重排重绘 */
  contain: layout style;
}

.chart-container:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.message-content {
  /* 使用contain属性优化渲染性能 */
  contain: layout style;
}

.message-text {
  /* 减少重排和重绘 */
  contain: layout;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* AI侧边栏样式 */
.ai-sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  z-index: 99999;
  display: flex;
  justify-content: flex-end;
  align-items: stretch;
  pointer-events: auto;
}

.ai-sidebar-panel {
  width: 800px;
  max-width: 45vw;
  height: 100vh;
  background: var(--el-bg-color);
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.3s ease-out;
  border-left: 1px solid var(--el-border-color-light);
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 100000;
  pointer-events: auto;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.ai-sidebar-header {
  background: linear-gradient(135deg, var(--el-color-primary-light-9), var(--el-color-primary-light-8));
  padding: 16px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  height: 60px;
}

.ai-sidebar-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.close-btn {
  color: var(--el-text-color-regular) !important;
  font-size: 20px;
  padding: 4px !important;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: var(--el-fill-color-light) !important;
  color: var(--el-text-color-primary) !important;
}

.ai-sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
  padding: 20px 24px 24px 24px;
  overflow: hidden;
}

.data-preview-section {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 16px;
  background: linear-gradient(135deg, var(--el-bg-color-page), var(--el-fill-color-lighter));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  flex-shrink: 0;
  max-height: 200px;
  overflow-y: auto;
}

.data-preview-section:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.data-preview-section h4 {
  margin: 0 0 12px 0;
  color: var(--el-text-color-primary);
  font-size: 15px;
  font-weight: 600;
}

.data-summary {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.data-details {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  border: none;
  border-radius: 0;
  padding: 12px 16px;
  background: var(--el-bg-color);
  box-shadow: none;
  position: relative;
  height: calc(100vh - 300px);
  display: flex;
  flex-direction: column;
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .chat-history {
    background: var(--el-bg-color);
  }
  
  .data-preview-section {
    background: linear-gradient(135deg, var(--el-fill-color-darker), var(--el-fill-color-dark));
    border-color: var(--el-border-color);
  }
  
  .message {
    border-bottom-color: var(--el-border-color);
  }
}

.message {
  display: flex;
  margin-bottom: 12px;
  align-items: flex-start;
  gap: 8px;
  animation: fadeInUp 0.3s ease-out;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row;
}

.message-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  box-shadow: none;
  border: none;
  margin-top: 2px;
}

.message.user .message-avatar {
  background: var(--el-color-primary);
  color: white;
}

.message.assistant .message-avatar {
  background: var(--el-color-success);
  color: white;
}

.message-content {
  flex: 1;
  max-width: calc(100% - 40px);
}

.message.user .message-content {
  text-align: left;
}

.message-text {
  background: transparent;
  padding: 0;
  border-radius: 0;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  box-shadow: none;
  border: none;
  position: relative;
  transition: none;
  color: var(--el-text-color-primary);
}



.message.user .message-text {
  background: transparent;
  border: none;
  color: var(--el-color-primary);
  font-weight: 500;
}

/* 移除消息气泡尾巴效果 */

/* 深色主题下的消息样式 */
@media (prefers-color-scheme: dark) {
  .message-text {
    background: transparent;
    border: none;
    box-shadow: none;
  }
  
  .message.user .message-text {
    background: transparent;
    color: var(--el-color-primary-light-3);
    border: none;
  }
}

/* Markdown样式 */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4),
.message-text :deep(h5),
.message-text :deep(h6) {
  margin: 12px 0 8px 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.message-text :deep(h1) { font-size: 18px; }
.message-text :deep(h2) { font-size: 16px; }
.message-text :deep(h3) { font-size: 15px; }
.message-text :deep(h4) { font-size: 14px; }

.message-text :deep(p) {
  margin: 8px 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-text :deep(code) {
  background: var(--el-color-info-light-9);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: var(--el-color-danger);
}

.message-text :deep(pre) {
  background: var(--el-color-info-light-9);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
  border: 1px solid var(--el-border-color-light);
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  color: var(--el-text-color-primary);
  font-size: 13px;
}

.message-text :deep(blockquote) {
  border-left: 4px solid var(--el-color-primary);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--el-text-color-regular);
  font-style: italic;
}

.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid var(--el-border-color);
  padding: 6px 8px;
  text-align: left;
}

.message-text :deep(th) {
  background: var(--el-bg-color-page);
  font-weight: 600;
}

.message-text :deep(strong) {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.message-text :deep(em) {
  font-style: italic;
}

.message-text :deep(a) {
  color: var(--el-color-primary);
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

.message-text :deep(hr) {
  border: none;
  border-top: 1px solid var(--el-border-color);
  margin: 16px 0;
}

/* AI思考块样式 */
.message-text :deep(.ai-thinking-block) {
  margin: 16px 0;
  border: 2px solid var(--el-color-warning-light-5);
  border-left: 4px solid var(--el-color-warning);
  border-radius: 8px;
  background: linear-gradient(135deg, 
    var(--el-color-warning-light-9) 0%, 
    var(--el-color-warning-light-8) 100%);
  box-shadow: 0 2px 8px rgba(230, 162, 60, 0.1);
  overflow: hidden;
  position: relative;
}

.message-text :deep(.ai-thinking-block::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    var(--el-color-warning), 
    var(--el-color-warning-light-3), 
    var(--el-color-warning));
  animation: thinking-glow 2s ease-in-out infinite;
}

@keyframes thinking-glow {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.message-text :deep(.thinking-header) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--el-color-warning-light-7);
  border-bottom: 1px solid var(--el-color-warning-light-4);
  font-weight: 600;
  font-size: 13px;
  color: var(--el-color-warning-dark-2);
}

.message-text :deep(.thinking-icon) {
  width: 16px;
  height: 16px;
  animation: thinking-pulse 1.5s ease-in-out infinite;
}

@keyframes thinking-pulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 1;
  }
  50% { 
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.message-text :deep(.thinking-label) {
  user-select: none;
}

.message-text :deep(.thinking-content) {
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--el-text-color-primary);
  background: var(--el-color-warning-light-9);
}

.message-text :deep(.thinking-content p) {
  margin: 8px 0;
}

.message-text :deep(.thinking-content p:first-child) {
  margin-top: 0;
}

.message-text :deep(.thinking-content p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(.thinking-content h1),
.message-text :deep(.thinking-content h2),
.message-text :deep(.thinking-content h3),
.message-text :deep(.thinking-content h4),
.message-text :deep(.thinking-content h5),
.message-text :deep(.thinking-content h6) {
  margin: 12px 0 8px 0;
  font-weight: 600;
  color: var(--el-color-warning-dark-2);
}

.message-text :deep(.thinking-content code) {
  background: var(--el-color-warning-light-8);
  color: var(--el-color-warning-dark-2);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.message-text :deep(.thinking-content pre) {
  background: var(--el-color-warning-light-8);
  border: 1px solid var(--el-color-warning-light-6);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(.thinking-content blockquote) {
  border-left: 4px solid var(--el-color-warning);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--el-color-warning-dark-2);
  font-style: italic;
}

.message-text :deep(.thinking-content ul),
.message-text :deep(.thinking-content ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(.thinking-content li) {
  margin: 4px 0;
}

/* 深色主题下的思考块样式 */
@media (prefers-color-scheme: dark) {
  .message-text :deep(.ai-thinking-block) {
    border-color: var(--el-color-warning-dark-2);
    background: linear-gradient(135deg, 
      rgba(230, 162, 60, 0.1) 0%, 
      rgba(230, 162, 60, 0.05) 100%);
  }
  
  .message-text :deep(.thinking-header) {
    background: rgba(230, 162, 60, 0.15);
    border-bottom-color: var(--el-color-warning-dark-2);
    color: var(--el-color-warning-light-3);
  }
  
  .message-text :deep(.thinking-content) {
    background: rgba(230, 162, 60, 0.08);
    color: var(--el-text-color-primary);
  }
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  gap: 8px;
  opacity: 0.7;
}

.message-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
  font-weight: 400;
}

.regenerate-btn {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.3s ease;
  opacity: 0.6;
  flex-shrink: 0;
  background: transparent;
  border: 1px solid var(--el-border-color-light);
}

.regenerate-btn:hover {
  opacity: 1;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.regenerate-btn :deep(.el-icon) {
  margin-right: 4px;
}

/* 只在assistant消息悬停时显示重新回答按钮 */
.message.assistant .regenerate-btn {
  opacity: 0;
  transition: all 0.3s ease;
}

.message.assistant:hover .regenerate-btn {
  opacity: 0.6;
}

.message.assistant:hover .regenerate-btn:hover {
  opacity: 0.9;
  background: var(--el-fill-color-light);
}

.input-section {
  border-top: 1px solid var(--el-border-color-light);
  padding-top: 20px;
  background: linear-gradient(to top, var(--el-bg-color), transparent);
  border-radius: 0 0 12px 12px;
  flex-shrink: 0;
  margin-top: auto;
}

.input-section :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 2px solid var(--el-border-color-light);
  transition: all 0.3s ease;
  background: var(--el-bg-color-page);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
}

.input-section :deep(.el-textarea__inner):focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1), inset 0 2px 4px rgba(0, 0, 0, 0.02);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: 16px;
  gap: 16px;
}

.quick-questions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.quick-questions :deep(.el-button) {
  border-radius: 20px;
  font-size: 12px;
  padding: 6px 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-light);
  color: var(--el-text-color-regular);
  transition: all 0.3s ease;
}

.quick-questions :deep(.el-button:hover) {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
  color: var(--el-color-primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.send-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.send-actions :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.send-actions :deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-light-3));
  border: none;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.send-actions :deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.send-actions :deep(.el-button--default) {
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color-light);
  color: var(--el-text-color-regular);
}

.send-actions :deep(.el-button--default:hover) {
  background: var(--el-fill-color);
  border-color: var(--el-border-color);
  transform: translateY(-1px);
}

.tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  font-style: italic;
  opacity: 0.8;
}

/* 深色主题下的输入区域样式 */
@media (prefers-color-scheme: dark) {
  .input-section :deep(.el-textarea__inner) {
    background: var(--el-fill-color-darker);
    border-color: var(--el-border-color);
  }
  
  .quick-questions :deep(.el-button) {
    background: var(--el-fill-color-dark);
    border-color: var(--el-border-color);
    color: var(--el-text-color-primary);
  }
  
  .send-actions :deep(.el-button--default) {
    background: var(--el-fill-color-dark);
    border-color: var(--el-border-color);
  }
}

/* 滚动条样式 */
.chat-history::-webkit-scrollbar {
  width: 8px;
}

.chat-history::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.chat-history::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--el-border-color-light), var(--el-border-color));
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.3s ease;
}

.chat-history::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--el-border-color), var(--el-border-color-dark));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 深色主题下的滚动条 */
@media (prefers-color-scheme: dark) {
  .chat-history::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--el-border-color), var(--el-border-color-dark));
    border-color: var(--el-border-color-darker);
  }
  
  .chat-history::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, var(--el-border-color-dark), var(--el-border-color-darker));
  }
}

/* 打字机光标动画效果 */
.typing-cursor {
  display: inline-block;
  color: var(--el-color-primary);
  font-weight: bold;
  font-size: 1.2em;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

/* 深色主题下的打字机光标 */
@media (prefers-color-scheme: dark) {
  .typing-cursor {
    color: var(--el-color-primary-light-3);
  }
}

/* 图表占位符样式 */
.message-text :deep(.chart-placeholder) {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  margin: 16px 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border: 2px dashed #d3d9df;
  border-radius: 12px;
  color: #666;
  font-size: 16px;
  transition: all 0.3s ease;
}

.message-text :deep(.placeholder-content) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.message-text :deep(.loading-dots::after) {
  content: '';
  animation: loadingDots 1.5s infinite;
}

@keyframes loadingDots {
  0% { content: ''; }
  25% { content: '.'; }
  50% { content: '..'; }
  75% { content: '...'; }
  100% { content: ''; }
}

/* 深色主题下的图表占位符 */
@media (prefers-color-scheme: dark) {
  .message-text :deep(.chart-placeholder) {
    background: linear-gradient(135deg, #2a2d3e 0%, #3e4358 100%);
    border-color: #4a4e63;
    color: #a0a4b8;
  }
}
</style>