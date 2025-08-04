<template>
  <el-dialog
    v-model="visible"
    title="编辑股票池"
    width="500px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="池名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入股票池名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          placeholder="请输入股票池描述（可选）"
          :rows="3"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
        >
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

// Props and Emits
const props = defineProps<{
  modelValue: boolean
  poolData: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'pool-updated': [pool: any]
}>()

// Data
const visible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance | null>(null)

const form = reactive({
  name: '',
  description: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入股票池名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

// Watch
watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
  if (!val) {
    resetForm()
  }
})

watch(() => props.poolData, (data) => {
  if (data) {
    form.name = data.name || ''
    form.description = data.description || ''
  }
}, { immediate: true })

// Methods
const resetForm = () => {
  form.name = ''
  form.description = ''
  formRef.value?.clearValidate()
}

const handleCancel = () => {
  visible.value = false
}

const handleSubmit = async () => {
  if (!formRef.value || !props.poolData) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const updatedPool = {
      ...props.poolData,
      name: form.name,
      description: form.description,
      updatedAt: new Date().toISOString()
    }
    
    emit('pool-updated', updatedPool)
    visible.value = false
  } catch (error) {
    console.error('更新股票池失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>