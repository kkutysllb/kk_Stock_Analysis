<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>配置系统参数和个人偏好</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 系统配置 -->
      <el-tab-pane label="系统配置" name="system">
        <el-form :model="systemConfig" label-width="120px">
          <el-form-item label="系统主题">
            <el-radio-group v-model="systemConfig.theme">
              <el-radio value="light">浅色主题</el-radio>
              <el-radio value="dark">深色主题</el-radio>
              <el-radio value="auto">跟随系统</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="自动保存">
            <el-switch v-model="systemConfig.autoSave" />
          </el-form-item>
          <el-form-item label="检查更新">
            <el-switch v-model="systemConfig.autoUpdate" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- AI智能配置 -->
      <el-tab-pane label="AI智能配置" name="ai">
        <el-form label-width="140px">
          <!-- 大模型配置 -->
          <el-divider content-position="left">大模型配置</el-divider>
          
          <el-form-item label="模型类型">
            <el-radio-group v-model="aiConfig.modelType">
              <el-radio value="online">在线大模型</el-radio>
              <el-radio value="local">本地大模型</el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 在线大模型配置 -->
          <template v-if="aiConfig.modelType === 'online'">
            <el-form-item label="在线模型提供商">
              <el-select v-model="aiConfig.onlineProvider" placeholder="请选择在线模型提供商">
                <el-option label="Deepseek" value="deepseek" />
                <el-option label="OpenAI" value="openai" />
                <el-option label="Claude" value="claude" />
                <el-option label="智谱AI" value="zhipu" />
                <el-option label="通义千问" value="qwen" />
                <el-option label="文心一言" value="wenxin" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="API地址">
              <el-input 
                v-model="aiConfig.onlineApiUrl" 
                placeholder="https://api.deepseek.com/v1/chat/completions"
                :disabled="aiConfig.onlineProvider !== 'custom'"
              />
            </el-form-item>
            
            <el-form-item label="API密钥">
              <el-input 
                v-model="aiConfig.onlineApiKey" 
                type="password" 
                placeholder="请输入API密钥"
                show-password
                @paste="handlePaste"
                clearable
              />
            </el-form-item>
            
            <el-form-item label="模型名称">
              <el-input 
                v-model="aiConfig.onlineModelName" 
                placeholder="deepseek-reasoner"
              />
            </el-form-item>
          </template>

          <!-- 本地大模型配置 -->
          <template v-if="aiConfig.modelType === 'local'">
            <el-form-item label="本地服务类型">
              <el-select v-model="aiConfig.localServiceType" placeholder="请选择本地服务类型">
                <el-option label="Ollama" value="ollama" />
                <el-option label="vLLM" value="vllm" />
                <el-option label="LM Studio" value="lm_studio" />
                <el-option label="自定义OpenAI兼容接口" value="custom_openai" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="服务地址">
              <el-input 
                v-model="aiConfig.localApiUrl" 
                :placeholder="getLocalServicePlaceholder()"
                clearable
              />
              <div class="form-item-description">{{ getLocalServiceDescription() }}</div>
            </el-form-item>
            
            <el-form-item label="API密钥">
              <el-input 
                v-model="aiConfig.localApiKey" 
                placeholder="本地服务通常不需要API密钥" 
                type="password" 
                show-password 
                clearable
                @paste="handleLocalPaste"
              />
            </el-form-item>
            
            <el-form-item label="模型名称">
              <el-input 
                v-model="aiConfig.localModelName" 
                :placeholder="getModelNamePlaceholder()"
                clearable
              />
              <div class="form-item-description">{{ getModelNameDescription() }}</div>
            </el-form-item>
            
            <!-- 快速配置按钮 -->
            <el-form-item label="快速配置">
              <div class="quick-config-buttons">
                <el-button size="small" @click="setOllamaDefaults">Ollama</el-button>
                <el-button size="small" @click="setLMStudioDefaults">LM Studio</el-button>
              </div>
              <div class="form-item-description">点击按钮快速设置对应服务的默认配置</div>
            </el-form-item>
          </template>

          <!-- 模型参数配置 -->
          <el-divider content-position="left">模型参数</el-divider>
          
          <el-form-item label="最大Token数">
            <el-input-number 
              v-model="aiConfig.maxTokens" 
              :min="100" 
              :max="32000" 
              :step="100"
            />
          </el-form-item>
          
          <el-form-item label="温度参数">
            <el-slider 
              v-model="aiConfig.temperature" 
              :min="0" 
              :max="2" 
              :step="0.1" 
              show-input
            />
          </el-form-item>
          
          <el-form-item label="超时时间(秒)">
            <el-input-number 
              v-model="aiConfig.timeout" 
              :min="10" 
              :max="300" 
              :step="10"
            />
          </el-form-item>

          <!-- 连接测试 -->
          <el-form-item label="连接测试">
            <div class="connection-test">
              <el-button 
                type="primary" 
                @click="testConnection" 
                :loading="testingConnection"
                :disabled="!aiConfig.localApiUrl && !aiConfig.onlineApiUrl"
                size="small"
              >
                测试连接
              </el-button>
              <div v-if="connectionStatus" class="connection-status" :class="connectionStatusClass">
                <div class="status-text">{{ connectionStatus }}</div>
                <div v-if="connectionStatus.includes('失败') && (aiConfig.localApiUrl?.includes('172.16.20.20') || aiConfig.onlineApiUrl?.includes('172.16.20.20'))" class="troubleshooting-tips">
                  <el-divider content-position="left">故障排除建议</el-divider>
                  <ul>
                     <li>检查172.16.20.20服务器是否在线</li>
                     <li>确认端口{{ extractPort(aiConfig.modelType === 'online' ? aiConfig.onlineApiUrl : aiConfig.localApiUrl) }}是否开放</li>
                     <li>验证网络连通性：ping 172.16.20.20</li>
                     <li>检查防火墙设置是否阻止连接</li>
                     <li>确认AI服务是否已在目标服务器启动</li>
                   </ul>
                   <div class="diagnostic-tools">
                     <el-button size="small" @click="runNetworkDiagnostic" :loading="diagnosticRunning">
                       运行网络诊断
                     </el-button>
                     <span v-if="diagnosticResult" class="diagnostic-result">{{ diagnosticResult }}</span>
                   </div>
                </div>
              </div>
            </div>
          </el-form-item>

          <!-- 功能配置 -->
          <el-divider content-position="left">功能配置</el-divider>
          
          <el-form-item label="智能分析">
            <el-switch v-model="aiConfig.enableAnalysis" />
            <span style="margin-left: 8px; color: #909399;">启用AI智能分析功能</span>
          </el-form-item>
          <el-form-item label="流式输出">
            <el-switch v-model="aiConfig.enableStreaming" />
            <span style="margin-left: 8px; color: #909399;">启用实时流式输出（推荐）</span>
          </el-form-item>
          <el-form-item label="内容优化">
            <el-switch v-model="aiConfig.contentOptimization" />
            <span style="margin-left: 8px; color: #909399;">自动优化生成的内容</span>
          </el-form-item>
          <el-form-item label="分析频率">
            <el-radio-group v-model="aiConfig.frequency">
              <el-radio value="realtime">实时分析</el-radio>
              <el-radio value="daily">每日分析</el-radio>
              <el-radio value="weekly">每周分析</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="准确度要求">
            <el-radio-group v-model="aiConfig.accuracy">
              <el-radio value="high">高精度</el-radio>
              <el-radio value="balanced">平衡模式</el-radio>
              <el-radio value="fast">快速模式</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <el-divider content-position="left">提示词模板</el-divider>
          
          <el-form-item label="模板类型">
            <el-select v-model="selectedTemplateType" placeholder="选择模板类型" style="width: 200px;">
              <el-option
                v-for="type in templateTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="模板操作">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
              <el-button type="primary" size="small" @click="previewPromptTemplate">
                预览提示词模板
              </el-button>
              <el-button type="success" size="small" @click="copyPromptTemplate">
                复制当前模板
              </el-button>
              <el-button type="info" size="small" @click="previewSystemPrompt">
              查看系统提示词
            </el-button>
            <el-button type="primary" size="small" @click="applySystemPrompt">
              应用系统提示词
            </el-button>
            <el-button type="success" size="small" @click="testAdaptivePrompts">
              测试自适应效果
            </el-button>
            </div>
            <div style="color: #909399; font-size: 12px; margin-top: 8px;">
              根据功能配置和模板类型生成专业提示词，系统提示词会自动应用到AI模型调用中
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-alert
              title="提示词说明"
              type="info"
              :closable="false"
              show-icon>
              <template #default>
                <div style="font-size: 13px; line-height: 1.5;">
                  • 系统会根据您的功能配置自动生成合适的AI提示词模板<br>
                  • 不同的分析频率、准确度要求会影响AI的回答风格<br>
                  • 启用智能分析和内容优化会让AI提供更深度的分析
                </div>
              </template>
            </el-alert>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 数据配置 -->
      <el-tab-pane label="数据配置" name="data">
        <el-form label-width="140px">
          <!-- 数据库连接配置 -->
          <el-divider content-position="left">数据库连接配置</el-divider>
          
          <!-- 云端数据库配置 -->
          <el-form-item label="云端数据库地址">
            <el-input 
              v-model="databaseConfig.cloud_database.host" 
              placeholder="118.195.242.207"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="云端数据库端口">
            <el-input-number 
              v-model="databaseConfig.cloud_database.port" 
              :min="1" 
              :max="65535" 
              placeholder="27017"
            />
          </el-form-item>
          
          <!-- 本地数据库配置 -->
          <el-form-item label="本地数据库地址">
            <el-input 
              v-model="databaseConfig.local_database.host" 
              placeholder="127.0.0.1"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="本地数据库端口">
            <el-input-number 
              v-model="databaseConfig.local_database.port" 
              :min="1" 
              :max="65535" 
              placeholder="27017"
            />
          </el-form-item>
          
          <!-- 数据库优先级 -->
          <el-form-item label="数据库优先级">
            <el-radio-group v-model="databaseConfig.priority">
              <el-radio value="local">本地优先</el-radio>
              <el-radio value="cloud">云端优先</el-radio>
            </el-radio-group>
            <div style="color: #909399; font-size: 12px; margin-top: 4px;">
              本地优先：优先使用本地数据库，失败时使用云端数据库
            </div>
          </el-form-item>
          
          <!-- 连接测试 -->
          <el-form-item label="连接测试">
            <div class="database-test-section">
              <div class="test-buttons">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="testDatabaseConnection('cloud_database')" 
                  :loading="testingCloudDB"
                >
                  测试云端数据库
                </el-button>
                <el-button 
                  type="success" 
                  size="small"
                  @click="testDatabaseConnection('local_database')" 
                  :loading="testingLocalDB"
                >
                  测试本地数据库
                </el-button>
                <el-button 
                  type="info" 
                  size="small"
                  @click="getDatabaseStatus" 
                  :loading="loadingDBStatus"
                >
                  获取状态
                </el-button>
              </div>
              
              <!-- 连接状态显示 -->
              <div v-if="databaseStatus" class="database-status">
                <el-divider content-position="left">数据库状态</el-divider>
                
                <div class="status-item">
                  <span class="status-label">云端数据库：</span>
                  <el-tag 
                    :type="databaseStatus.cloud_database.success ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ databaseStatus.cloud_database.success ? '连接正常' : '连接失败' }}
                  </el-tag>
                  <span class="status-message">{{ databaseStatus.cloud_database.message }}</span>
                </div>
                
                <div class="status-item">
                  <span class="status-label">本地数据库：</span>
                  <el-tag 
                    :type="databaseStatus.local_database.success ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ databaseStatus.local_database.success ? '连接正常' : '连接失败' }}
                  </el-tag>
                  <span class="status-message">{{ databaseStatus.local_database.message }}</span>
                </div>
                
                <div class="status-item">
                  <span class="status-label">当前使用：</span>
                  <el-tag 
                    :type="databaseStatus.active_database === 'none' ? 'danger' : 'success'"
                    size="small"
                  >
                    {{ getActiveDatabaseText(databaseStatus.active_database) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-form-item>
          
          <!-- 数据源配置 -->
          <el-divider content-position="left">数据源配置</el-divider>
          
          <el-form-item label="数据源">
            <el-radio-group v-model="dataConfig.source">
              <el-radio value="cloud">云端数据</el-radio>
              <el-radio value="local">本地数据</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="自动同步">
            <el-switch v-model="dataConfig.autoSync" />
            <span style="margin-left: 8px; color: #909399;">启用后会定期同步数据</span>
          </el-form-item>
          <el-form-item label="缓存时间">
            <el-input-number v-model="dataConfig.cacheTime" :min="1" :max="60" />
            <span style="margin-left: 8px;">分钟</span>
          </el-form-item>
          <el-form-item label="数据质量检查">
            <el-switch v-model="dataConfig.qualityCheck" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 内容生成配置 -->
      <el-tab-pane label="内容生成" name="content">
        <el-form :model="contentConfig" label-width="120px">
          <el-form-item label="默认平台">
            <el-select v-model="contentConfig.defaultPlatform">
              <el-option label="微信公众号" value="wechat" />
              <el-option label="小红书" value="xiaohongshu" />
              <el-option label="今日头条" value="toutiao" />
              <el-option label="抖音" value="douyin" />
            </el-select>
          </el-form-item>
          <el-form-item label="质量检查">
            <el-switch v-model="contentConfig.qualityCheck" />
          </el-form-item>
          <el-form-item label="自动发布">
            <el-switch v-model="contentConfig.autoPublish" />
          </el-form-item>
          <el-form-item label="内容备份">
            <el-switch v-model="contentConfig.backup" />
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <div class="settings-actions">
      <el-button type="primary" @click="saveSettings">保存设置</el-button>
      <el-button @click="resetSettings">重置设置</el-button>
      <el-button @click="exportSettings">导出配置</el-button>
      <el-button @click="importSettings">导入配置</el-button>
    </div>

    <!-- 提示词模板预览弹窗 -->
    <el-dialog
      v-model="showPromptDialog"
      title="提示词模板预览"
      width="70%"
      :before-close="() => showPromptDialog = false"
    >
      <div class="prompt-preview-content">
        <div class="prompt-header">
          <div class="template-info">
            <span class="template-type">模板类型：{{ templateTypes.find(t => t.value === selectedTemplateType)?.label }}</span>
            <span class="template-config">配置：{{ aiConfig.frequency }} | {{ aiConfig.accuracy }}</span>
          </div>
          <el-button type="primary" size="small" @click="copyPromptTemplate">
            复制模板
          </el-button>
        </div>
        <div class="prompt-content">
          <pre>{{ currentPromptTemplate }}</pre>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPromptDialog = false">关闭</el-button>
          <el-button type="primary" @click="copyPromptTemplate">复制到剪贴板</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  generateAnalysisPrompt, 
  generateContentPrompt,
  generateRealtimePrompt,
  generateTechnicalAnalysisPrompt,
  generateFundamentalAnalysisPrompt,
  getAvailableTemplateTypes,
  generatePromptByType
} from '@/utils/promptTemplates'
import {
  getCurrentSystemPrompt as getStoredSystemPrompt,
  generateSystemPromptFromConfig,
  updateSystemPrompt as saveSystemPrompt,
  getAIMessages,
  hasSystemPrompt
} from '@/utils/aiPromptManager'
import { runAllTests } from '@/utils/testAdaptivePrompts'
import { databaseConfigAPI, type DatabaseConfig, type DatabaseStatus } from '@/api/base'

const activeTab = ref('system')

const systemConfig = ref({
  theme: 'light',
  autoSave: true,
  autoUpdate: false
})

// AI配置数据
const aiConfig = ref({
  // 大模型配置
  modelType: 'online', // 'online' | 'local'
  
  // 在线大模型配置
  onlineProvider: 'deepseek',
  onlineApiUrl: 'https://api.deepseek.com/v1/chat/completions',
  onlineApiKey: '',
  onlineModelName: 'deepseek-reasoner',
  
  // 本地大模型配置
  localServiceType: 'ollama',
  localApiUrl: 'http://localhost:11434/v1/chat/completions',
  localModelName: 'qwen2.5:32b',
  localApiKey: '',
  
  // 模型参数
  maxTokens: 2000,
  temperature: 0.7,
  timeout: 60,
  
  // 功能配置
  enableAnalysis: true,
  enableStreaming: true,
  contentOptimization: true,
  frequency: 'daily' as 'realtime' | 'daily' | 'weekly',
  accuracy: 'balanced' as 'high' | 'balanced' | 'fast'
})

// 连接测试相关
const testingConnection = ref(false)
const connectionStatus = ref('')
const diagnosticRunning = ref(false)
const diagnosticResult = ref('')

// 预设的API配置
const providerConfigs: Record<string, { apiUrl: string; modelName: string }> = {
  deepseek: {
    apiUrl: 'https://api.deepseek.com/v1/chat/completions',
    modelName: 'deepseek-reasoner'
  },
  openai: {
    apiUrl: 'https://api.openai.com/v1/chat/completions',
    modelName: 'gpt-4'
  },
  claude: {
    apiUrl: 'https://api.anthropic.com/v1/messages',
    modelName: 'claude-3-sonnet-20240229'
  },
  zhipu: {
    apiUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    modelName: 'glm-4'
  },
  qwen: {
    apiUrl: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
    modelName: 'qwen-turbo'
  },
  wenxin: {
    apiUrl: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions',
    modelName: 'ernie-bot'
  }
}

// 监听在线提供商变化，自动更新配置
watch(() => aiConfig.value.onlineProvider, (newProvider) => {
  if (newProvider && newProvider !== 'custom' && providerConfigs[newProvider]) {
    aiConfig.value.onlineApiUrl = providerConfigs[newProvider].apiUrl
    aiConfig.value.onlineModelName = providerConfigs[newProvider].modelName
  }
})

// 监听本地服务类型变化，自动更新默认配置
watch(() => aiConfig.value.localServiceType, (newServiceType) => {
  if (newServiceType) {
    switch (newServiceType) {
      case 'ollama':
        aiConfig.value.localApiUrl = 'http://localhost:11434/v1/chat/completions'
        aiConfig.value.localModelName = 'qwen2.5:7b'
        break
      case 'lm_studio':
        aiConfig.value.localApiUrl = 'http://localhost:1234/v1/chat/completions'
        aiConfig.value.localModelName = 'local-model'
        break

      case 'vllm':
        aiConfig.value.localApiUrl = 'http://localhost:8000/v1/chat/completions'
        aiConfig.value.localModelName = 'local-model'
        break
      default:
        aiConfig.value.localApiUrl = 'http://localhost:8000/v1/chat/completions'
        aiConfig.value.localModelName = 'local-model'
    }
  }
})

// 获取本地服务地址提示信息
const getLocalServicePlaceholder = () => {
  switch (aiConfig.value.localServiceType) {
    case 'ollama':
      return 'http://localhost:11434/v1/chat/completions'
    case 'lm_studio':
      return 'http://localhost:1234/v1/chat/completions'

    case 'vllm':
      return 'http://localhost:8000/v1/chat/completions'
    default:
      return 'http://localhost:8000/v1/chat/completions'
  }
}

// 获取本地服务描述信息
const getLocalServiceDescription = () => {
  switch (aiConfig.value.localServiceType) {
    case 'ollama':
      return 'Ollama默认端口11434，确保已安装并启动Ollama服务'
    case 'lm_studio':
      return 'LM Studio默认端口1234，需要在LM Studio中启动本地服务器'

    case 'vllm':
      return 'vLLM默认端口8000，需要使用--host 0.0.0.0启动服务'
    default:
      return '请确保本地AI服务已启动并支持OpenAI兼容API'
  }
}

// 获取模型名称提示信息
const getModelNamePlaceholder = () => {
  switch (aiConfig.value.localServiceType) {
    case 'ollama':
      return 'qwen2.5:7b 或 llama3.1:8b'
    case 'lm_studio':
      return '在LM Studio中加载的模型名称'

    case 'vllm':
      return '启动vLLM时指定的模型名称'
    default:
      return 'local-model'
  }
}

// 获取模型名称描述信息
const getModelNameDescription = () => {
  switch (aiConfig.value.localServiceType) {
    case 'ollama':
      return '使用 ollama list 命令查看已安装的模型'
    case 'lm_studio':
      return '模型名称通常显示在LM Studio的服务器页面'

    case 'vllm':
      return '启动vLLM时--model参数指定的模型路径或名称'
    default:
      return '请参考具体服务的文档获取正确的模型名称'
  }
}

// 快速配置方法
const setOllamaDefaults = () => {
  aiConfig.value.localServiceType = 'ollama'
  aiConfig.value.localApiUrl = 'http://localhost:11434/v1/chat/completions'
  aiConfig.value.localModelName = 'qwen2.5:7b'
  aiConfig.value.localApiKey = ''
  ElMessage.success('已设置Ollama默认配置')
}

const setLMStudioDefaults = () => {
  aiConfig.value.localServiceType = 'lm_studio'
  aiConfig.value.localApiUrl = 'http://localhost:1234/v1/chat/completions'
  aiConfig.value.localModelName = 'local-model'
  aiConfig.value.localApiKey = ''
  ElMessage.success('已设置LM Studio默认配置')
}

// 提示词模板相关状态
const selectedTemplateType = ref('analysis')
const showPromptDialog = ref(false)
const currentPromptTemplate = ref('')

// 可用的提示词模板类型
const templateTypes = [
  { value: 'analysis', label: '基础分析' },
  { value: 'content', label: '内容创作' },
  { value: 'realtime', label: '实时分析' },
  { value: 'technical', label: '技术分析' },
  { value: 'fundamental', label: '基本面分析' },
  { value: 'system', label: '系统提示词' }
]

// 生成当前配置的提示词模板
const generateCurrentPrompt = (type: string = 'analysis') => {
  // 如果是系统提示词类型，直接返回系统提示词
  if (type === 'system') {
    return getCurrentSystemPrompt()
  }
  
  return generatePromptByType(type, {
    enableAnalysis: aiConfig.value.enableAnalysis,
    contentOptimization: aiConfig.value.contentOptimization,
    frequency: aiConfig.value.frequency,
    accuracy: aiConfig.value.accuracy
  }, {
    defaultPlatform: contentConfig.value?.defaultPlatform || 'wechat'
  })
}

// 获取当前提示词模板
const getCurrentPromptTemplate = computed(() => {
  return generateCurrentPrompt(selectedTemplateType.value)
})

// 预览提示词模板
const previewPromptTemplate = () => {
  currentPromptTemplate.value = generateCurrentPrompt(selectedTemplateType.value)
  showPromptDialog.value = true
}

// 复制提示词模板到剪贴板
const copyPromptTemplate = async () => {
  try {
    await navigator.clipboard.writeText(currentPromptTemplate.value)
    ElMessage.success('提示词模板已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 获取当前系统提示词（用于实际AI调用）
const getCurrentSystemPrompt = () => {
  return generateSystemPromptFromConfig({
    enableAnalysis: aiConfig.value.enableAnalysis,
    contentOptimization: aiConfig.value.contentOptimization,
    frequency: aiConfig.value.frequency,
    accuracy: aiConfig.value.accuracy
  })
}

// 监听功能配置变化，自动更新系统提示词
watch(
  () => [aiConfig.value.enableAnalysis, aiConfig.value.contentOptimization, aiConfig.value.frequency, aiConfig.value.accuracy],
  () => {
    // 当功能配置发生变化时，可以在这里触发相关更新
    // console.log('功能配置已更新，新的系统提示词：', getCurrentSystemPrompt()) 
  },
  { deep: true }
)

// 导出当前系统提示词（供其他组件使用）
const exportSystemPrompt = () => {
  const prompt = getCurrentSystemPrompt()
  // 可以通过事件总线或其他方式传递给需要的组件
  window.electronAPI?.updateSystemPrompt?.(prompt)
  return prompt
}

// 预览系统提示词
const previewSystemPrompt = () => {
  const systemPrompt = getCurrentSystemPrompt()
  currentPromptTemplate.value = systemPrompt
  selectedTemplateType.value = 'system' // 设置为系统模板类型
  showPromptDialog.value = true
}

// 应用系统提示词
const applySystemPrompt = () => {
  const systemPrompt = getCurrentSystemPrompt()
  
  try {
    saveSystemPrompt(systemPrompt)
    ElMessage.success('系统提示词已应用，将在下次AI调用时生效')
  } catch (error) {
    console.error('应用系统提示词失败:', error)
    ElMessage.error('应用系统提示词失败')
  }
}

// 获取已应用的系统提示词
const getAppliedSystemPrompt = () => {
  return getStoredSystemPrompt()
}

// 检查是否有已应用的系统提示词
const checkSystemPromptStatus = () => {
  return hasSystemPrompt()
}

// 测试自适应提示词效果
const testAdaptivePrompts = () => {
  try {
    // console.log('开始测试自适应提示词系统...')
    runAllTests()
    ElMessage.success('测试完成，请查看控制台输出结果')
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('测试失败，请检查控制台错误信息')
  }
}

// 处理在线API密钥粘贴事件
const handlePaste = (event: ClipboardEvent) => {
  // 阻止默认粘贴行为，避免重复粘贴
  event.preventDefault()
  event.stopPropagation()
  // 可以在这里添加额外的处理逻辑，比如验证粘贴内容格式
  const pastedText = event.clipboardData?.getData('text')
  if (pastedText) {
    // 移除可能的换行符和空格
    const cleanedText = pastedText.trim().replace(/\s+/g, '')
    // 更新到对应的输入框
    aiConfig.value.onlineApiKey = cleanedText
    ElMessage.success('在线API密钥已粘贴')
  }
}

// 处理本地API密钥粘贴事件
const handleLocalPaste = (event: ClipboardEvent) => {
  // 阻止默认粘贴行为，避免重复粘贴
  event.preventDefault()
  event.stopPropagation()
  const pastedText = event.clipboardData?.getData('text')
  if (pastedText) {
    // 移除可能的换行符和空格
    const cleanedText = pastedText.trim().replace(/\s+/g, '')
    // 更新到对应的输入框
    aiConfig.value.localApiKey = cleanedText
    ElMessage.success('本地API密钥已粘贴')
  }
}

// 连接状态样式
const connectionStatusClass = computed(() => {
  if (connectionStatus.value.includes('成功')) {
    return 'status-success'
  } else if (connectionStatus.value.includes('失败')) {
    return 'status-error'
  }
  return 'status-info'
})

// 提取端口号
const extractPort = (url: string) => {
  if (!url) return ''
  try {
    const urlObj = new URL(url)
    return urlObj.port || (urlObj.protocol === 'https:' ? '443' : '80')
  } catch {
    return ''
  }
}

const dataConfig = ref({
  source: 'cloud',
  autoSync: true,
  cacheTime: 10,
  qualityCheck: true
})

// 数据库配置
const databaseConfig = ref<DatabaseConfig>({
  cloud_database: {
    host: '118.195.242.207',
    port: 27017,
    database: 'quant_analysis'
  },
  local_database: {
    host: '127.0.0.1',
    port: 27017,
    database: 'quant_analysis'
  },
  priority: 'local'
})

// 数据库测试状态
const testingCloudDB = ref(false)
const testingLocalDB = ref(false)
const loadingDBStatus = ref(false)
const databaseStatus = ref<DatabaseStatus | null>(null)

const contentConfig = ref({
  defaultPlatform: 'wechat' as 'wechat' | 'xiaohongshu' | 'toutiao' | 'douyin',
  qualityCheck: true,
  autoPublish: false,
  backup: true
})

// 获取本地服务的健康检查端点
const getHealthCheckEndpoint = (serviceType: string, baseUrl: string) => {
  const url = new URL(baseUrl)
  const baseHost = `${url.protocol}//${url.host}`
  
  switch (serviceType) {
    case 'ollama':
      return `${baseHost}/api/tags` // Ollama的模型列表端点
    case 'vllm':
      return `${baseHost}/v1/models` // vLLM的模型列表端点
    case 'lm_studio':
      return `${baseHost}/v1/models` // LM Studio的模型列表端点

    default:
      return `${baseHost}/v1/models` // 默认OpenAI兼容端点
  }
}

// 简单的网络连通性检查
const checkNetworkConnectivity = async (url: string) => {
  try {
    const urlObj = new URL(url)
    const baseUrl = `${urlObj.protocol}//${urlObj.host}`
    
    // 尝试简单的HEAD请求检查连通性
    const response = await fetch(baseUrl, {
      method: 'HEAD',
      mode: 'no-cors', // 避免CORS问题
      signal: AbortSignal.timeout(5000) // 5秒超时
    })
    return true
  } catch (error) {
    // console.log('网络连通性检查失败:', error)
    return false
  }
}

// 运行网络诊断
const runNetworkDiagnostic = async () => {
  diagnosticRunning.value = true
  diagnosticResult.value = '正在诊断...'
  
  try {
    const currentUrl = aiConfig.value.modelType === 'online' ? aiConfig.value.onlineApiUrl : aiConfig.value.localApiUrl
    if (!currentUrl) {
      diagnosticResult.value = '请先配置API地址'
      return
    }
    
    const urlObj = new URL(currentUrl)
    const host = urlObj.hostname
    const port = urlObj.port || (urlObj.protocol === 'https:' ? '443' : '80')
    
    // 检查基础连通性
    const connectivityTests = []
    
    // 1. 尝试连接主机
    try {
      const baseResponse = await fetch(`${urlObj.protocol}//${urlObj.host}`, {
        method: 'HEAD',
        mode: 'no-cors',
        signal: AbortSignal.timeout(3000)
      })
      connectivityTests.push('✓ 主机可达')
    } catch {
      connectivityTests.push('✗ 主机不可达')
    }
    
    // 2. 尝试连接API端点
    try {
      const apiResponse = await fetch(currentUrl.replace('/chat/completions', '/models'), {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      })
      if (apiResponse.status < 500) {
        connectivityTests.push('✓ API端点响应')
      } else {
        connectivityTests.push('✗ API端点错误')
      }
    } catch {
      connectivityTests.push('✗ API端点无响应')
    }
    
    // 3. 检查端口（通过尝试连接）
    try {
      const portResponse = await fetch(`${urlObj.protocol}//${urlObj.host}`, {
        method: 'GET',
        signal: AbortSignal.timeout(2000)
      })
      connectivityTests.push(`✓ 端口${port}开放`)
    } catch {
      connectivityTests.push(`✗ 端口${port}可能被阻止`)
    }
    
    diagnosticResult.value = connectivityTests.join(' | ')
    
    // 如果是172.16.20.20，提供额外建议
    if (host === '172.16.20.20') {
      setTimeout(() => {
        ElMessage.info({
          message: '内网诊断完成。如果连接仍然失败，请联系网络管理员检查服务器状态。',
          duration: 5000
        })
      }, 1000)
    }
    
  } catch (error) {
    diagnosticResult.value = `诊断失败: ${error instanceof Error ? error.message : '未知错误'}`
  } finally {
    diagnosticRunning.value = false
  }
}

// 测试连接
const testConnection = async () => {
  testingConnection.value = true
  connectionStatus.value = '正在测试连接...'
  
  try {
    const config = aiConfig.value
    let apiUrl, apiKey, modelName, serviceType
    
    if (config.modelType === 'online') {
      apiUrl = config.onlineApiUrl
      apiKey = config.onlineApiKey
      modelName = config.onlineModelName
      serviceType = 'online'
    } else {
      apiUrl = config.localApiUrl
      apiKey = config.localApiKey || ''
      modelName = config.localModelName
      serviceType = config.localServiceType
    }
    
    if (!apiUrl) {
      connectionStatus.value = '请先配置API地址'
      return
    }
    
    // 对于本地服务，先进行基础网络连通性检查
    if (config.modelType === 'local') {
      connectionStatus.value = '正在检查网络连通性...'
      const isConnectable = await checkNetworkConnectivity(apiUrl)
      if (!isConnectable) {
        connectionStatus.value = '网络连通性检查失败，请检查服务地址和网络连接'
        return
      }
    }
    
    // 对于本地服务，先进行健康检查
    if (config.modelType === 'local') {
      try {
        const healthEndpoint = getHealthCheckEndpoint(serviceType, apiUrl)
        // console.log(`正在检查服务健康状态: ${healthEndpoint}`)
        
        // 根据服务类型调整超时时间
        const healthTimeout = serviceType === 'ollama' ? 15000 : 10000 // Ollama需要更长时间
        
        const healthResponse = await fetch(healthEndpoint, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
          },
          signal: AbortSignal.timeout(healthTimeout)
        })
        
        if (!healthResponse.ok) {
          const errorText = await healthResponse.text()
          connectionStatus.value = `服务不可用: ${healthResponse.status} ${healthResponse.statusText}`
          console.error('健康检查失败:', errorText)
          
          // 提供具体的故障排除建议
          if (healthResponse.status === 404) {
            connectionStatus.value += ' - 请检查服务是否已启动，端口是否正确'
          } else if (healthResponse.status === 403) {
            connectionStatus.value += ' - 请检查API密钥是否正确'
          }
          return
        }
        
        // console.log('健康检查通过，开始测试聊天接口')
      } catch (healthError) {
        console.error('健康检查异常:', healthError)
        connectionStatus.value = `无法连接到服务: ${healthError instanceof Error ? healthError.message : '网络错误'}`
        return
      }
    }
    
    // 构建请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    
    // 根据服务类型设置认证头
    if (config.modelType === 'online' || (config.modelType === 'local' && apiKey)) {
      headers['Authorization'] = `Bearer ${apiKey}`
    }
    
    // 构建请求体
    const requestBody: any = {
      model: modelName,
      messages: [{
        role: 'user',
        content: '你好，这是一个连接测试。请简单回复确认。'
      }],
      max_tokens: 20,
      temperature: 0.1
    }
    
    // 对于Ollama，使用不同的请求格式
    if (config.modelType === 'local' && serviceType === 'ollama') {
      // Ollama使用不同的API端点
      const ollamaUrl = apiUrl.replace('/v1/chat/completions', '/api/generate')
      requestBody.prompt = '你好，这是一个连接测试。请简单回复确认。'
      requestBody.stream = false
      delete requestBody.messages
      
      // console.log(`使用Ollama格式请求: ${ollamaUrl}`)
      
      const response = await fetch(ollamaUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: AbortSignal.timeout(config.timeout * 1000)
      })
      
      if (response.ok) {
        const result = await response.json()
        connectionStatus.value = '连接成功！'
        // ElMessage.success(`AI模型连接测试成功 (${serviceType})`)
        // console.log('Ollama响应:', result)
      } else {
        const errorText = await response.text()
        connectionStatus.value = `连接失败: ${response.status} ${response.statusText}`
        // console.error('Ollama连接测试失败:', errorText)
      }
      return
    }
    
    // 发送标准OpenAI格式的测试请求
    // console.log(`发送测试请求到: ${apiUrl}`)
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
      signal: AbortSignal.timeout(config.timeout * 1000)
    })
    
    if (response.ok) {
      const result = await response.json()
      connectionStatus.value = '连接成功！'
      // ElMessage.success(`AI模型连接测试成功 (${config.modelType === 'online' ? config.onlineProvider : serviceType})`)
      // console.log('API响应:', result)
      
      // 连接测试成功后自动保存配置
      saveSettings()
    } else {
      const errorText = await response.text()
      let errorMsg = `连接失败: ${response.status} ${response.statusText}`
      
      // 提供更详细的错误信息和解决建议
      if (response.status === 404) {
        errorMsg += ' - API端点不存在，请检查URL路径是否正确'
      } else if (response.status === 401) {
        errorMsg += ' - 认证失败，请检查API密钥'
      } else if (response.status === 403) {
        errorMsg += ' - 权限不足，请检查API密钥权限'
      } else if (response.status === 422) {
        errorMsg += ' - 请求参数错误，请检查模型名称'
      } else if (response.status >= 500) {
        errorMsg += ' - 服务器内部错误，请稍后重试'
      }
      
      connectionStatus.value = errorMsg
      console.error('连接测试失败:', errorText)
    }
  } catch (error) {
    let errorMessage = '未知错误'
    
    if (error instanceof Error) {
      if (error.name === 'AbortError' || error.message.includes('aborted')) {
        errorMessage = `请求超时 (${aiConfig.value.timeout}秒)，请检查：\n1. 服务地址是否正确\n2. 服务是否已启动\n3. 网络连接是否正常\n4. 可尝试增加超时时间`
      } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorMessage = '网络连接失败，请检查：\n1. 服务地址格式是否正确\n2. 服务是否已启动\n3. 端口是否被占用或防火墙阻止'
      } else if (error.message.includes('ECONNREFUSED')) {
        errorMessage = '连接被拒绝，请检查：\n1. 服务是否已启动\n2. 端口号是否正确\n3. 服务是否绑定到正确的地址'
      } else if (error.message.includes('ENOTFOUND')) {
        errorMessage = '域名解析失败，请检查服务地址是否正确'
      } else {
        errorMessage = error.message
      }
    }
    
    connectionStatus.value = `连接失败: ${errorMessage}`
    console.error('连接测试错误:', error)
    
    // 针对172.16.20.20地址的特殊提示
    const currentApiUrl = aiConfig.value.modelType === 'online' ? aiConfig.value.onlineApiUrl : aiConfig.value.localApiUrl
    if (currentApiUrl && currentApiUrl.includes('172.16.20.20')) {
      ElMessage.warning('检测到内网地址，请确保：\n1. 网络连通性正常\n2. 服务已在目标机器上启动\n3. 防火墙允许访问该端口')
    }
  } finally {
    testingConnection.value = false
  }
}

// 保存设置到本地存储
const saveSettings = async () => {
  try {
    // 保存到localStorage
    localStorage.setItem('kk-stock-system-config', JSON.stringify(systemConfig.value))
    localStorage.setItem('kk-stock-ai-config', JSON.stringify(aiConfig.value))
    localStorage.setItem('kk-stock-data-config', JSON.stringify(dataConfig.value))
    localStorage.setItem('kk-stock-content-config', JSON.stringify(contentConfig.value))
    
    // 保存数据库配置到后端
    await saveDatabaseConfig()
    
    ElMessage.success('设置已保存')
    
    // 触发全局事件，通知其他组件配置已更新
    window.dispatchEvent(new CustomEvent('ai-config-updated', {
      detail: aiConfig.value
    }))
  } catch (error) {
    ElMessage.error('保存设置失败')
    console.error('保存设置错误:', error)
  }
}

// 从本地存储加载设置
const loadSettings = () => {
  try {
    const savedSystemConfig = localStorage.getItem('kk-stock-system-config')
    const savedAiConfig = localStorage.getItem('kk-stock-ai-config')
    const savedDataConfig = localStorage.getItem('kk-stock-data-config')
    const savedContentConfig = localStorage.getItem('kk-stock-content-config')
    
    if (savedSystemConfig) {
      Object.assign(systemConfig.value, JSON.parse(savedSystemConfig))
    }
    if (savedAiConfig) {
      Object.assign(aiConfig.value, JSON.parse(savedAiConfig))
    }
    if (savedDataConfig) {
      Object.assign(dataConfig.value, JSON.parse(savedDataConfig))
    }
    if (savedContentConfig) {
      Object.assign(contentConfig.value, JSON.parse(savedContentConfig))
    }
  } catch (error) {
    console.error('加载设置错误:', error)
  }
}

const resetSettings = () => {
  // 重置为默认值
  systemConfig.value = {
    theme: 'light',
    autoSave: true,
    autoUpdate: false
  }
  
  aiConfig.value = {
    modelType: 'online',
    onlineProvider: 'deepseek',
    onlineApiUrl: 'https://api.deepseek.com/v1/chat/completions',
    onlineApiKey: '',
    onlineModelName: 'deepseek-reasoner',
    localServiceType: 'ollama',
    localApiUrl: 'http://localhost:11434/v1/chat/completions',
    localModelName: 'qwen2.5:32b',
    localApiKey: '',
    maxTokens: 2000,
    temperature: 0.7,
    timeout: 60,
    enableAnalysis: true,
    enableStreaming: true,
    contentOptimization: true,
    frequency: 'daily',
    accuracy: 'balanced'
  }
  
  dataConfig.value = {
    source: 'cloud',
    autoSync: true,
    cacheTime: 10,
    qualityCheck: true
  }
  
  contentConfig.value = {
    defaultPlatform: 'wechat',
    qualityCheck: true,
    autoPublish: false,
    backup: true
  }
  
  connectionStatus.value = ''
  ElMessage.info('设置已重置')
}

const exportSettings = () => {
  try {
    const settings = {
      system: systemConfig.value,
      ai: aiConfig.value,
      data: dataConfig.value,
      content: contentConfig.value,
      exportTime: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `kk-stock-settings-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    ElMessage.success('配置已导出')
  } catch (error) {
    ElMessage.error('导出配置失败')
    console.error('导出配置错误:', error)
  }
}

const importSettings = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  
  input.onchange = async (event) => {
    const target = event.target as HTMLInputElement
    const file = target?.files?.[0]
    if (!file) return
    
    try {
      const text = await file.text()
      const settings = JSON.parse(text)
      
      if (settings.system) Object.assign(systemConfig.value, settings.system)
      if (settings.ai) Object.assign(aiConfig.value, settings.ai)
      if (settings.data) Object.assign(dataConfig.value, settings.data)
      if (settings.content) Object.assign(contentConfig.value, settings.content)
      
      ElMessage.success('配置已导入')
    } catch (error) {
      ElMessage.error('导入配置失败，请检查文件格式')
      console.error('导入配置错误:', error)
    }
  }
  
  input.click()
}

// 数据库相关方法
const testDatabaseConnection = async (dbType: 'cloud_database' | 'local_database') => {
  try {
    if (dbType === 'cloud_database') {
      testingCloudDB.value = true
    } else {
      testingLocalDB.value = true
    }
    
    const response = await databaseConfigAPI.testConnection({ db_type: dbType })
    
    if (response.success) {
      ElMessage.success(`${dbType === 'cloud_database' ? '云端' : '本地'}数据库连接成功`)
    } else {
      ElMessage.error(`${dbType === 'cloud_database' ? '云端' : '本地'}数据库连接失败: ${response.data?.message}`)
    }
    
    // 测试完成后刷新状态
    await getDatabaseStatus()
    
  } catch (error) {
    console.error('测试数据库连接失败:', error)
    ElMessage.error(`测试${dbType === 'cloud_database' ? '云端' : '本地'}数据库连接失败`)
  } finally {
    if (dbType === 'cloud_database') {
      testingCloudDB.value = false
    } else {
      testingLocalDB.value = false
    }
  }
}

const getDatabaseStatus = async () => {
  try {
    loadingDBStatus.value = true
    const response = await databaseConfigAPI.getStatus()
    
    if (response.success && response.data) {
      databaseStatus.value = response.data
    } else {
      ElMessage.error('获取数据库状态失败')
    }
  } catch (error) {
    console.error('获取数据库状态失败:', error)
    ElMessage.error('获取数据库状态失败')
  } finally {
    loadingDBStatus.value = false
  }
}

const getActiveDatabaseText = (activeDB: string) => {
  switch (activeDB) {
    case 'local_database':
      return '本地数据库'
    case 'cloud_database':
      return '云端数据库'
    case 'none':
      return '无可用数据库'
    default:
      return '未知状态'
  }
}

const loadDatabaseConfig = async () => {
  try {
    const response = await databaseConfigAPI.getConfig()
    if (response.success && response.data) {
      databaseConfig.value = response.data
    }
  } catch (error) {
    console.error('加载数据库配置失败:', error)
  }
}

const saveDatabaseConfig = async () => {
  try {
    const response = await databaseConfigAPI.updateConfig({
      cloud_database: {
        host: databaseConfig.value.cloud_database.host,
        port: databaseConfig.value.cloud_database.port
      },
      local_database: {
        host: databaseConfig.value.local_database.host,
        port: databaseConfig.value.local_database.port
      },
      priority: databaseConfig.value.priority
    })
    
    if (response.success) {
      ElMessage.success('数据库配置保存成功')
      
      // 保存后重新加载后端配置
      try {
        const reloadResponse = await databaseConfigAPI.reloadConfig()
        if (reloadResponse.success) {
          // console.log('后端数据库配置重新加载成功')
          ElMessage.success('数据库配置已生效，数据查询将使用新配置')
        } else {
          // console.warn('后端配置重新加载失败:', reloadResponse)
          ElMessage.warning('配置已保存，但后端重新加载失败，请手动重启API服务')
        }
      } catch (reloadError) {
        console.error('重新加载后端配置失败:', reloadError)
        ElMessage.warning('配置已保存，但后端重新加载失败，请手动重启API服务')
      }
      
      // 刷新状态
      await getDatabaseStatus()
    } else {
      ElMessage.error('数据库配置保存失败')
    }
  } catch (error) {
    console.error('保存数据库配置失败:', error)
    ElMessage.error('保存数据库配置失败')
  }
}

// 组件挂载时加载设置
onMounted(() => {
  loadSettings()
  loadDatabaseConfig()
  getDatabaseStatus()
})
</script>

<style scoped>
.settings-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0 0 8px 0;
}

.page-header p {
  color: #606266;
  margin: 0;
}

.settings-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.settings-actions .el-button {
  margin-right: 12px;
}

.form-item-description {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.quick-config-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-config-buttons .el-button {
  margin: 0;
}

.connection-test {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.connection-status {
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  background-color: #f8f9fa;
}

.connection-status.status-success {
  border-color: #67c23a;
  background-color: #f0f9ff;
  color: #67c23a;
}

.connection-status.status-error {
  border-color: #f56c6c;
  background-color: #fef0f0;
  color: #f56c6c;
}

.connection-status.status-info {
  border-color: #909399;
  background-color: #f4f4f5;
  color: #909399;
}

.status-text {
  font-weight: 500;
  margin-bottom: 8px;
}

.troubleshooting-tips {
  margin-top: 12px;
  padding: 12px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.troubleshooting-tips ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
  color: #606266;
}

.troubleshooting-tips li {
   margin-bottom: 4px;
   font-size: 13px;
   line-height: 1.4;
 }
 
 .diagnostic-tools {
   margin-top: 12px;
   padding: 8px 0;
   border-top: 1px solid #e4e7ed;
   display: flex;
   align-items: center;
   gap: 12px;
 }
 
 .diagnostic-result {
   font-size: 12px;
   color: #606266;
   font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
   background-color: #f5f7fa;
   padding: 4px 8px;
   border-radius: 4px;
   border: 1px solid #e4e7ed;
   max-width: 400px;
   overflow-x: auto;
   white-space: nowrap;
 }

.prompt-preview-content {
  max-height: 60vh;
  overflow-y: auto;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.template-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-type {
  font-weight: 600;
  color: #303133;
}

.template-config {
  font-size: 12px;
  color: #909399;
}

.prompt-content {
  background-color: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.prompt-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 数据库配置相关样式 */
.database-test-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.test-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.database-status {
  margin-top: 16px;
  padding: 12px;
  background-color: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-label {
  font-weight: 500;
  min-width: 80px;
  color: #303133;
}

.status-message {
  font-size: 12px;
  color: #606266;
  margin-left: 8px;
}
</style>