<template>
  <div class="max-w-4xl mx-auto">
    <div class="bg-white rounded-xl shadow-card overflow-hidden">
      <div class="p-6 border-b border-gray-border">
        <h2 class="text-lg font-semibold text-text-primary">智能问答</h2>
        <p class="text-sm text-text-secondary mt-1">基于企业制度文档的智能问答助手</p>
      </div>
      
      <div ref="messagesContainer" class="h-[500px] overflow-y-auto p-6 space-y-4">
        <div v-if="messages.length === 0" class="text-center py-16">
          <div class="w-16 h-16 bg-gray-bg rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p class="text-text-secondary">请输入您的问题开始对话</p>
          <p class="text-sm text-text-secondary mt-2">例如：今年我司的带薪年假有多少天？</p>
        </div>
        
        <div v-for="(message, index) in messages" :key="index" class="space-y-4">
          <div class="flex justify-end">
            <div class="bg-primary text-white px-4 py-3 rounded-lg rounded-br-sm max-w-[80%]">
              <p>{{ message.question }}</p>
            </div>
          </div>
          
          <div class="flex justify-start">
            <div class="bg-gray-bg px-4 py-3 rounded-lg rounded-bl-sm max-w-[80%]">
              <p class="text-text-primary whitespace-pre-wrap">{{ message.answer }}</p>
              
              <div v-if="message.sources && message.sources.length > 0" class="mt-4 pt-4 border-t border-gray-border">
                <p class="text-sm font-medium text-text-secondary mb-2">参考来源：</p>
                <div class="space-y-2">
                  <div 
                    v-for="(source, sIndex) in message.sources" 
                    :key="sIndex"
                    class="bg-white p-3 rounded-lg text-sm"
                  >
                    <div class="flex items-center gap-2 mb-1">
                      <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span class="font-medium text-text-primary">{{ source.source }}</span>
                      <span v-if="source.section" class="text-xs text-primary bg-blue-50 px-2 py-0.5 rounded">
                        {{ source.section }}
                      </span>
                      <span v-if="source.chunk_index !== null && source.chunk_index !== undefined" class="text-text-secondary text-xs">
                        (片段 {{ source.chunk_index + 1 }})
                      </span>
                      <span class="text-text-secondary text-xs">相关度: {{ (source.relevance_score * 100).toFixed(0) }}%</span>
                    </div>
                    <p class="text-text-secondary line-clamp-2">{{ source.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="loading" class="flex justify-start">
          <div class="bg-gray-bg px-4 py-3 rounded-lg">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              <span class="text-text-secondary ml-2">正在思考...</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="p-6 border-t border-gray-border bg-gray-bg">
        <div class="flex gap-3">
          <input
            v-model="inputQuestion"
            type="text"
            placeholder="请输入您的问题..."
            class="flex-1 px-4 py-3 rounded-lg border border-gray-border focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
            @keyup.enter="sendMessage"
            :disabled="loading"
          />
          <button
            @click="sendMessage"
            :disabled="loading || !inputQuestion.trim()"
            class="px-6 py-3 bg-primary text-white rounded-lg font-medium hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            发送
          </button>
        </div>
      </div>
    </div>
    
    <FileUpload @upload-success="onUploadSuccess" class="mt-6" />
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { sendMessage as sendMessageApi } from '../services/api'
import FileUpload from '../components/FileUpload.vue'

const messages = ref([])
const inputQuestion = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputQuestion.value.trim() || loading.value) return
  
  const question = inputQuestion.value.trim()
  inputQuestion.value = ''
  loading.value = true
  
  try {
    const response = await sendMessageApi(question)
    messages.value.push({
      question,
      answer: response.data.answer,
      sources: response.data.sources
    })
    await scrollToBottom()
  } catch (error) {
    messages.value.push({
      question,
      answer: error.response?.data?.detail || '发送消息失败，请稍后重试',
      sources: []
    })
  } finally {
    loading.value = false
  }
}

const onUploadSuccess = (data) => {
  messages.value.push({
    question: `上传文档: ${data.filename}`,
    answer: `文档上传成功！已解析 ${data.chunks_count} 个文本片段，现在可以针对该文档进行提问了。`,
    sources: []
  })
  scrollToBottom()
}
</script>
