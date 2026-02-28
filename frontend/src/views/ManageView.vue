<template>
  <div class="max-w-4xl mx-auto">
    <div class="bg-white rounded-xl shadow-card overflow-hidden">
      <div class="p-6 border-b border-gray-border">
        <h2 class="text-lg font-semibold text-text-primary">文档管理</h2>
        <p class="text-sm text-text-secondary mt-1">管理已上传的企业制度文档</p>
      </div>
      
      <div v-if="loading" class="p-12 text-center">
        <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p class="text-text-secondary mt-4">加载中...</p>
      </div>
      
      <div v-else-if="documents.length === 0" class="p-12 text-center">
        <svg class="w-16 h-16 text-gray-border mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-text-secondary">暂无文档</p>
        <p class="text-sm text-text-secondary mt-2">请前往智能问答页面上传文档</p>
      </div>
      
      <div v-else class="divide-y divide-gray-border">
        <div 
          v-for="doc in documents" 
          :key="doc.id"
          class="p-6 hover:bg-gray-bg transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h3 class="font-medium text-text-primary">{{ doc.filename }}</h3>
                <div class="flex items-center gap-4 mt-2 text-sm text-text-secondary">
                  <span>上传时间: {{ doc.upload_time }}</span>
                  <span>文本片段: {{ doc.chunks_count }} 个</span>
                  <span>文件大小: {{ formatFileSize(doc.file_size) }}</span>
                </div>
              </div>
            </div>
            
            <button
              @click="deleteDocument(doc)"
              class="p-2 text-text-secondary hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              :disabled="deleting === doc.id"
            >
              <svg v-if="deleting === doc.id" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="documents.length > 0" class="mt-6 bg-white rounded-xl shadow-card p-6">
      <h3 class="font-medium text-text-primary mb-4">统计信息</h3>
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-gray-bg rounded-lg p-4 text-center">
          <p class="text-2xl font-semibold text-primary">{{ documents.length }}</p>
          <p class="text-sm text-text-secondary mt-1">文档总数</p>
        </div>
        <div class="bg-gray-bg rounded-lg p-4 text-center">
          <p class="text-2xl font-semibold text-primary">{{ totalChunks }}</p>
          <p class="text-sm text-text-secondary mt-1">文本片段</p>
        </div>
        <div class="bg-gray-bg rounded-lg p-4 text-center">
          <p class="text-2xl font-semibold text-primary">{{ formatFileSize(totalSize) }}</p>
          <p class="text-sm text-text-secondary mt-1">总大小</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDocuments as fetchDocuments, deleteDocument as deleteDocumentApi } from '../services/api'

const documents = ref([])
const loading = ref(true)
const deleting = ref(null)

const totalChunks = computed(() => {
  return documents.value.reduce((sum, doc) => sum + doc.chunks_count, 0)
})

const totalSize = computed(() => {
  return documents.value.reduce((sum, doc) => sum + doc.file_size, 0)
})

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const loadDocuments = async () => {
  try {
    const response = await fetchDocuments()
    documents.value = response.data.documents
  } catch (error) {
    console.error('加载文档列表失败:', error)
  } finally {
    loading.value = false
  }
}

const deleteDocument = async (doc) => {
  if (!confirm(`确定要删除文档 "${doc.filename}" 吗？删除后无法恢复。`)) {
    return
  }
  
  deleting.value = doc.id
  try {
    await deleteDocumentApi(doc.id)
    documents.value = documents.value.filter(d => d.id !== doc.id)
  } catch (error) {
    alert(error.response?.data?.detail || '删除失败，请稍后重试')
  } finally {
    deleting.value = null
  }
}

onMounted(() => {
  loadDocuments()
})
</script>
