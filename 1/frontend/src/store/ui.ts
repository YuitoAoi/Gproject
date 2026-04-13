import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const isCollapsed = ref(false)
  
  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
  }
  
  const setSidebarCollapsed = (collapsed: boolean) => {
    isCollapsed.value = collapsed
  }
  
  return {
    isCollapsed,
    toggleSidebar,
    setSidebarCollapsed
  }
})