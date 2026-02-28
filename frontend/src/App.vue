<template>
  <div class="min-h-screen bg-white flex">
    <Sidebar />
    <main class="flex-1 ml-64 p-8">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
</script>
