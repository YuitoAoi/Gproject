import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import HomeView from '@/views/HomeView.vue'
import DashboardView from '@/views/DashboardView.vue'
import DataManagementView from '@/views/DataManagementView.vue'
import TrainingView from '@/views/TrainingView.vue'
import ModelsView from '@/views/ModelsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomeView
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView
        },
        {
          path: 'data-management',
          name: 'data-management',
          component: DataManagementView
        },
        {
          path: 'training',
          name: 'training',
          component: TrainingView
        },
        {
          path: 'models',
          name: 'models',
          component: ModelsView
        }
      ]
    }
  ]
})

export default router
