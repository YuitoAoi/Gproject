import { AppRouteRecord } from '@/types/router'

export const workbenchRoutes: AppRouteRecord = {
  name: 'Workbench',
  path: '/workbench',
  component: '/index/index',
  meta: {
    title: 'menus.workbench.title',
    icon: 'ri:dashboard-3-fill',
    roles: ['R_SUPER', 'R_ADMIN']
  },
  children: [
    {
      path: 'overview',
      name: 'Overview',
      component: '/workbench/overview',
      meta: {
        title: 'menus.workbench.overview',
        icon: 'ri:home-smile-2-line',
        keepAlive: false,
        fixedTab: true,
        roles: ['R_SUPER', 'R_ADMIN']
      }
    },
    {
      path: 'compute-storage',
      name: 'ComputeStorage',
      component: '/workbench/compute-storage',
      meta: {
        title: 'menus.workbench.computeStorage',
        icon: 'ri:computer-line',
        keepAlive: false,
        roles: ['R_SUPER', 'R_ADMIN']
      }
    },
    {
      path: 'task-dispatch',
      name: 'TaskDispatch',
      component: '/workbench/task-dispatch',
      meta: {
        title: 'menus.workbench.taskDispatch',
        icon: 'ri:timer-flash-line',
        keepAlive: false,
        roles: ['R_SUPER', 'R_ADMIN']
      }
    }
  ]
}

export const dataManagementRoutes: AppRouteRecord = {
  name: 'DataManagement',
  path: '/data-management',
  component: '/data-management/index',
  meta: {
    title: 'menus.dataManagement.title',
    icon: 'ri:folder-open-line',
    roles: ['R_SUPER', 'R_ADMIN']
  }
}

export const modelTrainingRoutes: AppRouteRecord = {
  name: 'ModelTraining',
  path: '/model-training',
  component: '/model-training/index',
  meta: {
    title: 'menus.modelTraining.title',
    icon: 'ri:brain-line',
    roles: ['R_SUPER', 'R_ADMIN']
  }
}

export const taskMonitoringRoutes: AppRouteRecord = {
  name: 'TaskMonitoring',
  path: '/task-monitoring',
  component: '/task-monitoring/index',
  meta: {
    title: 'menus.taskMonitoring.title',
    icon: 'ri:line-chart-line',
    roles: ['R_SUPER', 'R_ADMIN']
  }
}

export const modelInferenceRoutes: AppRouteRecord = {
  name: 'ModelInference',
  path: '/model-inference',
  component: '/model-inference/index',
  meta: {
    title: 'menus.modelInference.title',
    icon: 'ri:chat-3-line',
    roles: ['R_SUPER', 'R_ADMIN']
  }
}
