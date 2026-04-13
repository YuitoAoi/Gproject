import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import(/* webpackChunkName: "dashboard" */ '../views/DashboardView.vue')
  },
  {
    path: '/data-management',
    name: 'DataManagement',
    component: () => import(/* webpackChunkName: "data-management" */ '../views/DataManagementView.vue')
  },
  {
    path: '/training/tasks',
    name: 'TrainingTasks',
    component: () => import(/* webpackChunkName: "training-tasks" */ '../views/training/TasksView.vue')
  },
  {
    path: '/training/models',
    name: 'TrainingModels',
    component: () => import(/* webpackChunkName: "training-models" */ '../views/training/ModelsView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router