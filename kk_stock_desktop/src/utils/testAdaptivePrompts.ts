/**
 * 自适应提示词系统测试工具
 * 用于测试不同功能配置下生成的提示词效果
 */

import { generateSystemPromptFromConfig, getAIMessages, getCurrentSystemPrompt } from './aiPromptManager'

// 测试不同配置组合
export const testPromptConfigurations = () => {
  console.log('=== 自适应提示词系统测试 ===')
  
  // 测试配置1：高频实时分析
  const config1 = {
    enableAnalysis: true,
    contentOptimization: true,
    frequency: 'realtime' as const,
    accuracy: 'high' as const
  }
  
  console.log('\n配置1 - 高频实时分析:')
  console.log(generateSystemPromptFromConfig(config1))
  
  // 测试配置2：平衡日度分析
  const config2 = {
    enableAnalysis: true,
    contentOptimization: false,
    frequency: 'daily' as const,
    accuracy: 'balanced' as const
  }
  
  console.log('\n配置2 - 平衡日度分析:')
  console.log(generateSystemPromptFromConfig(config2))
  
  // 测试配置3：快速周度分析
  const config3 = {
    enableAnalysis: false,
    contentOptimization: false,
    frequency: 'weekly' as const,
    accuracy: 'fast' as const
  }
  
  console.log('\n配置3 - 快速周度分析:')
  console.log(generateSystemPromptFromConfig(config3))
}

// 测试数据上下文增强
export const testDataContextEnhancement = () => {
  console.log('\n=== 数据上下文增强测试 ===')
  
  const dataContext = {
    dataType: '股票日线数据',
    dataName: '平安银行(000001)',
    period: '2024年1月-12月',
    summary: '全年涨幅15.2%，成交量活跃',
    data: { price: 12.5, volume: 1000000 }
  }
  
  const enhancedPrompt = getCurrentSystemPrompt(dataContext)
  console.log('增强后的提示词:')
  console.log(enhancedPrompt)
  
  // 测试AI消息构建
  const messages = getAIMessages('请分析这只股票的投资价值', dataContext)
  console.log('\nAI消息数组:')
  console.log(JSON.stringify(messages, null, 2))
}

// 测试提示词适应性
export const testPromptAdaptability = () => {
  console.log('\n=== 提示词适应性测试 ===')
  
  const scenarios = [
    {
      name: '技术分析场景',
      config: { enableAnalysis: true, contentOptimization: true, frequency: 'realtime', accuracy: 'high' },
      context: { dataType: 'K线数据', dataName: 'MACD指标', period: '日线' }
    },
    {
      name: '基本面分析场景', 
      config: { enableAnalysis: true, contentOptimization: true, frequency: 'weekly', accuracy: 'high' },
      context: { dataType: '财务数据', dataName: '年报数据', period: '2024年' }
    },
    {
      name: '快速查询场景',
      config: { enableAnalysis: false, contentOptimization: false, frequency: 'daily', accuracy: 'fast' },
      context: { dataType: '实时行情', dataName: '上证指数', period: '当前' }
    }
  ]
  
  scenarios.forEach(scenario => {
    console.log(`\n--- ${scenario.name} ---`)
    const prompt = getCurrentSystemPrompt(scenario.context)
    console.log(prompt.substring(0, 200) + '...')
  })
}

// 运行所有测试
export const runAllTests = () => {
  testPromptConfigurations()
  testDataContextEnhancement()
  testPromptAdaptability()
  console.log('\n=== 测试完成 ===')
}