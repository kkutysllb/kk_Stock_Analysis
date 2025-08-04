<template>
  <el-dialog
    v-model="visible"
    title="创建股票池"
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
          创建
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import type { FormInstance, FormRules } from 'element-plus'

// 股票池接口定义
interface StockPool {
  id: string
  name: string
  description: string
  stocks: string[]
  createdAt: string
  updatedAt: string
}

// Props and Emits
const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'pool-created': [pool: StockPool]
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
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 调用后端API创建股票池
    const response = await axios.post('/user/stock-pools/create', {
      pool_name: form.name,
      description: form.description,
      pool_type: 'custom',
      is_default: false,
      is_public: false,
      is_deletable: true,
      tags: [],
      stocks: []
    })
    
    // 后端直接返回StockPoolResponse对象
    const newPool: StockPool = {
      id: response.data.pool_id,
      name: response.data.pool_name,
      description: response.data.description,
      stocks: response.data.stocks || [],
      createdAt: response.data.create_time,
      updatedAt: response.data.update_time
    }
    
    emit('pool-created', newPool)
    visible.value = false
    ElMessage.success('股票池创建成功')
  } catch (error: any) {
    console.error('创建股票池失败:', error)
    if (error.response?.status === 400) {
      ElMessage.error(error.response.data.message || '请求参数有误')
    } else if (error.response?.status === 401) {
      ElMessage.error('请先登录')
    } else if (error.response?.status === 409) {
      ElMessage.error('股票池名称已存在，请更换名称')
    } else {
      ElMessage.error('创建股票池时发生错误，请稍后重试')
    }
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