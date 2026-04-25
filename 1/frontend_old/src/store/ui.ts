import { defineStore } from 'pinia'
import { ref } from 'vue'
import httpClient from '@/api/httpClient'

export const useUIStore = defineStore('ui', () => {
  const isCollapsed = ref(false)
  const connected = ref(false)

  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
  }

  const checkBackendConnection = async () => {
    try {
      await httpClient.get('/health')
      connected.value = true
    } catch {
      connected.value = false
    }
  }

  return {
    isCollapsed,
    connected,
    toggleSidebar,
    checkBackendConnection
  }
})
