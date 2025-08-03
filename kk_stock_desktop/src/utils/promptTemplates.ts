/**
 * 提示词模板管理工具
 * 根据AI配置动态生成不同的提示词模板
 */

export interface AIConfig {
  enableAnalysis: boolean
  contentOptimization: boolean
  frequency: 'realtime' | 'daily' | 'weekly'
  accuracy: 'high' | 'balanced' | 'fast'
}

export interface ContentConfig {
  defaultPlatform: 'wechat' | 'xiaohongshu' | 'toutiao' | 'douyin'
}

/**
 * 基础提示词模板
 */
const BASE_TEMPLATES = {
  system: '你是一个专业的股票量化分析助手。',
  analysis: {
    enabled: '请提供深度的技术分析和基本面分析。',
    disabled: '请提供基础的市场信息和数据解读。'
  },
  optimization: {
    enabled: '请确保回答结构清晰、逻辑严谨，并提供可操作的建议。',
    disabled: ''
  },
  frequency: {
    realtime: '重点关注实时市场动态和短期趋势变化。',
    daily: '重点关注日内走势和当日重要事件影响。',
    weekly: '重点关注周期性趋势和中期投资机会。'
  },
  accuracy: {
    high: '请提供详细的数据支撑和多维度分析，确保分析的准确性和可靠性。',
    balanced: '请在分析深度和效率之间保持平衡，提供实用的投资建议。',
    fast: '请快速提供核心观点和关键信息，突出重点。'
  }
}

/**
 * 内容平台特定的提示词模板
 */
const PLATFORM_TEMPLATES = {
  wechat: {
    style: '请使用适合微信公众号的写作风格，内容要有吸引力且易于阅读。',
    format: '建议使用小标题、要点列表等格式提升可读性。',
    length: '内容长度控制在800-1500字之间。'
  },
  xiaohongshu: {
    style: '请使用年轻化、生活化的表达方式，适合小红书用户群体。',
    format: '可以使用emoji表情和话题标签增加互动性。',
    length: '内容简洁明了，控制在500-800字。'
  },
  toutiao: {
    style: '请使用新闻化的表达方式，突出时效性和重要性。',
    format: '标题要有吸引力，内容要有明确的观点。',
    length: '内容详实，控制在1000-2000字。'
  },
  douyin: {
    style: '请使用简洁有力的表达方式，适合短视频脚本。',
    format: '重点突出，节奏明快，易于理解。',
    length: '内容精炼，控制在200-500字。'
  }
}

/**
 * 生成基础分析提示词模板
 */
export function generateAnalysisPrompt(config: AIConfig): string {
  let prompt = BASE_TEMPLATES.system
  
  // 添加分析能力配置
  prompt += config.enableAnalysis 
    ? BASE_TEMPLATES.analysis.enabled 
    : BASE_TEMPLATES.analysis.disabled
  
  // 添加内容优化配置
  if (config.contentOptimization) {
    prompt += BASE_TEMPLATES.optimization.enabled
  }
  
  // 添加分析频率配置
  prompt += BASE_TEMPLATES.frequency[config.frequency]
  
  // 添加准确度要求配置
  prompt += BASE_TEMPLATES.accuracy[config.accuracy]
  
  return prompt
}

/**
 * 生成内容创作提示词模板
 */
export function generateContentPrompt(aiConfig: AIConfig, contentConfig: ContentConfig): string {
  let prompt = generateAnalysisPrompt(aiConfig)
  
  const platformTemplate = PLATFORM_TEMPLATES[contentConfig.defaultPlatform]
  
  prompt += `\n\n内容创作要求：\n`
  prompt += `• ${platformTemplate.style}\n`
  prompt += `• ${platformTemplate.format}\n`
  prompt += `• ${platformTemplate.length}`
  
  return prompt
}

/**
 * 生成实时分析提示词模板
 */
export function generateRealtimePrompt(config: AIConfig): string {
  let prompt = BASE_TEMPLATES.system
  prompt += '当前是实时分析模式，请重点关注：\n'
  prompt += '• 最新的市场动态和价格变化\n'
  prompt += '• 突发事件对市场的即时影响\n'
  prompt += '• 短期交易机会和风险提示\n'
  
  if (config.accuracy === 'fast') {
    prompt += '• 快速给出核心观点，避免冗长分析\n'
  }
  
  return prompt
}

/**
 * 生成技术分析提示词模板
 */
export function generateTechnicalAnalysisPrompt(config: AIConfig): string {
  let prompt = BASE_TEMPLATES.system
  prompt += '请进行专业的技术分析，包括：\n'
  prompt += '• K线形态和趋势分析\n'
  prompt += '• 技术指标信号解读\n'
  prompt += '• 支撑阻力位判断\n'
  prompt += '• 成交量分析\n'
  
  if (config.accuracy === 'high') {
    prompt += '• 提供详细的技术指标数据和计算依据\n'
    prompt += '• 多时间周期综合分析\n'
  }
  
  return prompt
}

/**
 * 生成基本面分析提示词模板
 */
export function generateFundamentalAnalysisPrompt(config: AIConfig): string {
  let prompt = BASE_TEMPLATES.system
  prompt += '请进行深入的基本面分析，包括：\n'
  prompt += '• 公司财务状况分析\n'
  prompt += '• 行业发展趋势\n'
  prompt += '• 宏观经济影响\n'
  prompt += '• 估值水平评估\n'
  
  if (config.accuracy === 'high') {
    prompt += '• 提供具体的财务数据和比率分析\n'
    prompt += '• 同行业对比分析\n'
  }
  
  return prompt
}

/**
 * 获取所有可用的提示词模板类型
 */
export function getAvailableTemplateTypes(): string[] {
  return [
    'analysis', // 基础分析
    'content', // 内容创作
    'realtime', // 实时分析
    'technical', // 技术分析
    'fundamental' // 基本面分析
  ]
}

/**
 * 根据类型生成对应的提示词模板
 */
export function generatePromptByType(
  type: string, 
  aiConfig: AIConfig, 
  contentConfig?: ContentConfig
): string {
  switch (type) {
    case 'analysis':
      return generateAnalysisPrompt(aiConfig)
    case 'content':
      return contentConfig 
        ? generateContentPrompt(aiConfig, contentConfig)
        : generateAnalysisPrompt(aiConfig)
    case 'realtime':
      return generateRealtimePrompt(aiConfig)
    case 'technical':
      return generateTechnicalAnalysisPrompt(aiConfig)
    case 'fundamental':
      return generateFundamentalAnalysisPrompt(aiConfig)
    default:
      return generateAnalysisPrompt(aiConfig)
  }
}