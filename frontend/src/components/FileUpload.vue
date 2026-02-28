<template>
  <div
    class="bg-white rounded-xl shadow-card p-6"
    :class="{ 'border-2 border-dashed border-primary': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-text-primary">上传文档</h3>
      <span class="text-sm text-text-secondary">支持 PDF、Word 格式</span>
    </div>
    
    <div class="relative">
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.doc,.docx"
        class="hidden"
        @change="handleFileSelect"
      />
      
      <div
        @click="$refs.fileInput.click()"
        class="border-2 border-dashed border-gray-border rounded-lg p-8 text-center cursor-pointer hover:border-primary hover:bg-gray-bg transition-all"
      >
        <svg class="w-12 h-12 text-text-secondary mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="text-text-primary font-medium">点击或拖拽文件到此处上传</p>
        <p class="text-sm text-text-secondary mt-2">最大文件大小: 10MB</p>
      </div>
    </div>
    
    <div v-if="uploading" class="mt-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-text-secondary">{{ currentFileName }}</span>
        <span class="text-sm text-primary">{{ uploadProgress }}%</span>
      </div>
      <div class="w-full bg-gray-border rounded-full h-2">
        <div 
          class="bg-primary h-2 rounded-full transition-all duration-300"
          :style="{ width: `${uploadProgress}%` }"
        ></div>
      </div>
    </div>
    
    <div v-if="uploadStatus" class="mt-4 p-3 rounded-lg" :class="uploadStatus.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
      {{ uploadStatus.message }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadDocument } from '../services/api'

const emit = defineEmits(['upload-success'])

const fileInput = ref(null)
const isDragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const currentFileName = ref('')
const uploadStatus = ref(null)

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    doUploadFile(file)
  }
}

const handleDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    doUploadFile(file)
  }
}

const doUploadFile = async (file) => {
  uploading.value = true
  uploadProgress.value = 0
  currentFileName.value = file.name
  uploadStatus.value = null
  
  try {
    const response = await uploadDocument(file, (progress) => {
      uploadProgress.value = progress
    })
    
    uploadStatus.value = {
      success: true,
      message: `文档上传成功！共解析 ${response.data.chunks_count} 个文本片段`
    }
    
    emit('upload-success', response.data)
  } catch (error) {
    uploadStatus.value = {
      success: false,
      message: error.response?.data?.detail || '上传失败，请稍后重试'
    }
  } finally {
    uploading.value = false
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
}
</script>
