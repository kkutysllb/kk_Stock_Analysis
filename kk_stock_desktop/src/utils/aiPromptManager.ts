/**
 * AI提示词管理工具
 * 用于管理和获取根据用户配置生成的AI提示词
 */

import type { ElectronAPI } from '../types/electron'

export interface AIConfig {
  enableAnalysis: boolean
  contentOptimization: boolean
  frequency: 'realtime' | 'daily' | 'weekly'
  accuracy: 'high' | 'balanced' | 'fast'
}

/**
 * 获取当前应用的系统提示词
 * @param dataContext 可选的数据上下文信息
 * @returns 当前系统提示词
 */
export const getCurrentSystemPrompt = (dataContext?: {
  dataType?: string
  dataName?: string
  period?: string
  summary?: string
  data?: any
}): string => {
  try {
    // 首先尝试从本地存储获取已应用的提示词
    const storedPrompt = localStorage.getItem('currentSystemPrompt')
    let basePrompt = storedPrompt
    
    if (!basePrompt) {
       // 如果没有存储的提示词，生成默认的
       basePrompt = generateSystemPromptFromConfig({
         enableAnalysis: true,
         contentOptimization: true,
         frequency: 'daily',
         accuracy: 'balanced'
       })
     }
    
    // 如果提供了数据上下文，则增强提示词
    if (dataContext) {
      basePrompt += '\n\n当前数据上下文：'
      
      if (dataContext.dataType) {
        basePrompt += `\n- 数据类型: ${dataContext.dataType}`
      }
      if (dataContext.dataName) {
        basePrompt += `\n- 数据名称: ${dataContext.dataName}`
      }
      if (dataContext.period) {
        basePrompt += `\n- 时间周期: ${dataContext.period}`
      }
      if (dataContext.summary) {
        basePrompt += `\n- 数据摘要: ${dataContext.summary}`
      }
      
      basePrompt += '\n\n请基于以上数据上下文回答问题，重点突出关键信息。需要图表时使用ECharts格式：'
      basePrompt += '\n```json'
      basePrompt += '\n{"title":{"text":"标题"},"xAxis":{"data":["A"]},"yAxis":{},"series":[{"type":"line","data":[1]}]}'
      basePrompt += '\n```'
    }
    
    return basePrompt
  } catch (error) {
    console.error('获取系统提示词失败:', error)
    return generateDefaultSystemPrompt()
  }
}

/**
 * 根据配置生成系统提示词
 * @param config AI配置
 * @returns 生成的系统提示词
 */
export const generateSystemPromptFromConfig = (config: AIConfig): string => {
  let systemPrompt = '你是一个专业的股票量化分析助手。'
  
  // 根据智能分析配置调整提示词
  if (config.enableAnalysis) {
    systemPrompt += '请提供深度的技术分析和基本面分析，包括详细的数据解读和投资建议。'
  } else {
    systemPrompt += '请提供基础的市场信息和数据解读。'
  }
  
  // 根据内容优化配置调整提示词
  if (config.contentOptimization) {
    systemPrompt += '请确保回答结构清晰、逻辑严谨，并提供可操作的建议。使用专业术语时请适当解释。'
  }
  
  // 根据分析频率调整提示词
  switch (config.frequency) {
    case 'realtime':
      systemPrompt += '重点关注实时市场动态和短期趋势变化，提供及时的交易信号和风险提示。'
      break
    case 'daily':
      systemPrompt += '重点关注日内走势和当日重要事件影响，提供当日交易策略建议。'
      break
    case 'weekly':
      systemPrompt += '重点关注周期性趋势和中期投资机会，提供中长期投资策略。'
      break
  }
  
  // 根据准确度要求调整提示词
  switch (config.accuracy) {
    case 'high':
      systemPrompt += '请提供详细的数据支撑和多维度分析，确保分析的准确性和可靠性。引用具体的技术指标和财务数据。'
      break
    case 'balanced':
      systemPrompt += '请在分析深度和效率之间保持平衡，提供实用的投资建议，重点突出关键信息。'
      break
    case 'fast':
      systemPrompt += '请快速提供核心观点和关键信息，突出重点，简洁明了地表达主要结论。'
      break
  }
  
  return systemPrompt
}

/**
 * 生成默认系统提示词
 * @returns 默认系统提示词
 */
const generateDefaultSystemPrompt = (): string => {
  return generateSystemPromptFromConfig({
    enableAnalysis: true,
    contentOptimization: true,
    frequency: 'daily',
    accuracy: 'balanced'
  })
}

/**
 * 更新系统提示词
 * @param prompt 新的系统提示词
 */
export const updateSystemPrompt = (prompt: string): void => {
  try {
    localStorage.setItem('currentSystemPrompt', prompt)
    
    // 如果有electron API，也通过它更新
    if (window.electronAPI?.updateSystemPrompt) {
      window.electronAPI.updateSystemPrompt(prompt)
    }
    
    console.log('系统提示词已更新:', prompt)
  } catch (error) {
    console.error('更新系统提示词失败:', error)
  }
}

/**
 * 清除系统提示词
 */
export const clearSystemPrompt = (): void => {
  try {
    localStorage.removeItem('currentSystemPrompt')
    console.log('系统提示词已清除')
  } catch (error) {
    console.error('清除系统提示词失败:', error)
  }
}

/**
 * 获取用于AI调用的消息数组
 * @param userMessage 用户消息
 * @param dataContext 可选的数据上下文信息
 * @returns 包含系统提示词和用户消息的数组
 */
export const getAIMessages = (userMessage: string, dataContext?: {
  dataType?: string
  dataName?: string
  period?: string
  summary?: string
  data?: any
}) => {
  const systemPrompt = getCurrentSystemPrompt(dataContext)
  
  return [
    {
      role: 'system',
      content: systemPrompt
    },
    {
      role: 'user', 
      content: userMessage
    }
  ]
}

/**
 * 检查系统提示词是否已设置
 * @returns 是否已设置系统提示词
 */
export const hasSystemPrompt = (): boolean => {
  try {
    const prompt = localStorage.getItem('currentSystemPrompt')
    return !!prompt
  } catch (error) {
    return false
  }
}

// 类型声明已在 electron.d.ts 中定义