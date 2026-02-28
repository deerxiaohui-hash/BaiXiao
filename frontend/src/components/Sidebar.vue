<template>
  <aside class="fixed left-0 top-0 h-full w-64 bg-gray-bg border-r border-gray-border flex flex-col">
    <div class="p-6 border-b border-gray-border">
      <h1 class="text-xl font-semibold text-text-primary">智能问答知识库</h1>
      <p class="text-sm text-text-secondary mt-1">企业制度文档助手</p>
    </div>
    
    <nav class="flex-1 p-4">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-all duration-200"
        :class="[
          $route.path === item.path
            ? 'bg-primary text-white shadow-soft'
            : 'text-text-secondary hover:bg-white hover:text-text-primary'
        ]"
      >
        <component :is="item.icon" class="w-5 h-5" />
        <span class="font-medium">{{ item.name }}</span>
      </router-link>
    </nav>
    
    <div class="p-4 border-t border-gray-border">
      <div class="bg-white rounded-lg p-4 shadow-soft">
        <p class="text-sm text-text-secondary">使用提示</p>
        <p class="text-xs text-text-secondary mt-2 leading-relaxed">
          上传企业制度文档后，即可通过自然语言提问获取答案
        </p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { h } from 'vue'

const ChatIcon = () => h('svg', { 
  xmlns: 'http://www.w3.org/2000/svg', 
  fill: 'none', 
  viewBox: '0 0 24 24', 
  'stroke-width': '1.5', 
  stroke: 'currentColor' 
}, [
  h('path', { 
    'stroke-linecap': 'round', 
    'stroke-linejoin': 'round', 
    d: 'M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z' 
  })
])

const FolderIcon = () => h('svg', { 
  xmlns: 'http://www.w3.org/2000/svg', 
  fill: 'none', 
  viewBox: '0 0 24 24', 
  'stroke-width': '1.5', 
  stroke: 'currentColor' 
}, [
  h('path', { 
    'stroke-linecap': 'round', 
    'stroke-linejoin': 'round', 
    d: 'M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z' 
  })
])

const menuItems = [
  { name: '智能问答', path: '/', icon: ChatIcon },
  { name: '文档管理', path: '/manage', icon: FolderIcon }
]
</script>
