<template>
  <el-dialog
    v-model="visible"
    title="分析设置"
    width="500px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="form"
      label-width="120px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="包含成交量分析">
        <el-switch 
          v-model="form.includeVolume"
          active-text="开启"
          inactive-text="关闭"
        />
        <div class="setting-description">
          分析成交量模式和量价关系
        </div>
      </el-form-item>
      
      <el-form-item label="包含技术指标">
        <el-switch 
          v-model="form.includeTechnical"
          active-text="开启"
          inactive-text="关闭"
        />
        <div class="setting-description">
          包含MACD、RSI、移动平均线等技术指标
        </div>
      </el-form-item>
      
      <el-form-item label="分析时间周期">
        <el-checkbox-group v-model="form.timeframes">
          <el-checkbox label="daily">日线</el-checkbox>
          <el-checkbox label="weekly">周线</el-checkbox>
          <el-checkbox label="monthly">月线</el-checkbox>
        </el-checkbox-group>
        <div class="setting-description">
          选择要分析的时间周期
        </div>
      </el-form-item>
      
      <el-form-item label="信心阈值">
        <el-slider 
          v-model="form.confidenceThreshold" 
          :min="0" 
          :max="100" 
          :step="5"
          show-input
          :show-input-controls="false"
        />
        <div class="setting-description">
          低于此阈值的分析结果将被标记为低信心
        </div>
      </el-form-item>
      
      <!-- 分析深度设置已移除 -->
      
      <el-form-item label="数据回溯期">
        <el-select v-model="form.lookbackPeriod" placeholder="选择数据回溯期">
          <el-option label="3个月" value="3m" />
          <el-option label="6个月" value="6m" />
          <el-option label="1年" value="1y" />
          <el-option label="2年" value="2y" />
        </el-select>
        <div class="setting-description">
          分析时使用的历史数据时间范围
        </div>
      </el-form-item>
      
      <el-form-item label="风险评估">
        <el-switch 
          v-model="form.enableRiskAssessment"
          active-text="开启"
          inactive-text="关闭"
        />
        <div class="setting-description">
          包含止损位、目标位和仓位建议
        </div>
      </el-form-item>
      
      <el-form-item label="自动保存结果">
        <el-switch 
          v-model="form.autoSaveResults"
          active-text="开启"
          inactive-text="关闭"
        />
        <div class="setting-description">
          自动保存分析结果到历史记录
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="resetToDefault">恢复默认</el-button>
        <el-button @click="handleCancel">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
        >
          保存设置
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'

// Props and Emits
const props = defineProps<{
  modelValue: boolean
  settings: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'settings-updated': [settings: any]
}>()

// Data
const visible = ref(false)
const formRef = ref<FormInstance | null>(null)

const form = reactive({
  includeVolume: true,
  includeTechnical: true,
  timeframes: ['daily', 'weekly'],
  confidenceThreshold: 60,
  lookbackPeriod: '1y',
  enableRiskAssessment: true,
  autoSaveResults: true
})

// Default settings
const defaultSettings = {
  includeVolume: true,
  includeTechnical: true,
  timeframes: ['daily', 'weekly'],
  confidenceThreshold: 60,
  lookbackPeriod: '1y',
  enableRiskAssessment: true,
  autoSaveResults: true
}

// Watch
watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

watch(() => props.settings, (settings) => {
  if (settings) {
    Object.assign(form, settings)
  }
}, { immediate: true, deep: true })

// Methods
const resetToDefault = () => {
  Object.assign(form, defaultSettings)
}

const handleCancel = () => {
  // 恢复到原始设置
  if (props.settings) {
    Object.assign(form, props.settings)
  }
  visible.value = false
}

const handleSubmit = () => {
  // 验证设置
  if (form.timeframes.length === 0) {
    ElMessage.warning('请至少选择一个分析时间周期')
    return
  }
  
  // 发送更新的设置
  const updatedSettings = { ...form }
  emit('settings-updated', updatedSettings)
}
</script>

<style scoped>
.setting-description {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
  line-height: 1.4;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
}

.dialog-footer > div {
  display: flex;
  gap: var(--spacing-sm);
}

/* Element Plus 样式覆盖 */
:deep(.el-form-item__label) {
  color: var(--text-primary);
  font-weight: 500;
}

:deep(.el-checkbox__label) {
  color: var(--text-primary);
}

:deep(.el-radio__label) {
  color: var(--text-primary);
}

:deep(.el-switch__action) {
  background: white;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: var(--accent-primary);
  border-color: var(--accent-primary);
}

:deep(.el-slider__runway) {
  background: var(--bg-elevated);
}

:deep(.el-slider__bar) {
  background: var(--accent-primary);
}

:deep(.el-slider__button) {
  border-color: var(--accent-primary);
}

:deep(.el-input-number) {
  width: 80px;
}

:deep(.el-input-number .el-input__inner) {
  text-align: center;
}
</style>