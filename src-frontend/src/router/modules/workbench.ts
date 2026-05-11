import { AppRouteRecord } from '@/types/router'

export const workbenchRoutes: AppRouteRecord = {
  name: 'Workbench',
  path: '/workbench',
  component: '/index/index',
  meta: {
    title: 'menus.workbench.title',
    icon: 'ri:settings-4-line',
    roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
  },
  children: [
    {
      path: 'dashboard',
      name: 'Dashboard',
      component: '/workbench/dashboard',
      meta: {
        title: 'menus.workbench.dashboard',
        icon: 'ri:home-smile-2-line',
        keepAlive: false,
        fixedTab: true,
        roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
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
        roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
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
        roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
      },
      children: [
        {
          path: 'task-monitoring/:id',
          name: 'TaskMonitoringDetail',
          component: '/task-monitoring/index',
          meta: {
            title: 'menus.taskMonitoring.detail',
            keepAlive: false,
            hideInMenu: true,
            roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
          }
        }
      ]
    }
  ]
}

export const dataManagementRoutes: AppRouteRecord = {
  name: 'DataManagement',
  path: '/data-management',
  component: '/index/index',
  meta: {
    title: 'menus.dataManagement.title',
    icon: 'ri:folder-open-line',
    roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
  },
  children: [
    {
      path: 'dataset-hub',
      name: 'DatasetHub',
      component: '/data-management/dataset-hub',
      meta: {
        title: 'menus.dataManagement.datasetHub',
        icon: 'ri:database-2-line',
        keepAlive: false,
        roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
      }
    },
    {
      path: 'data-processing',
      name: 'DataProcessing',
      component: '/data-management/data-processing',
      meta: {
        title: 'menus.dataManagement.dataProcessing',
        icon: 'ri:refresh-line',
        keepAlive: true,
        roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
      }
    }
  ]
}

export const modelFactoryRoutes: AppRouteRecord = {
  name: 'ModelFactory',
  path: '/model-factory',
  component: '/index/index',
  meta: {
    title: 'menus.modelFactory.title',
    icon: 'ri:cpu-line',
    roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
  },
  children: [
    {
      path: 'new-training',
      name: 'NewTraining',
      component: '/model-factory/new-training',
      meta: {
        title: 'menus.modelFactory.newTraining',
        icon: 'ri:rocket-line',
        keepAlive: false,
        roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
      }
    },
    {
      path: 'model-registry',
      name: 'ModelRegistry',
      component: '/model-factory/model-registry',
      meta: {
        title: 'menus.modelFactory.modelRegistry',
        icon: 'ri:archive-line',
        keepAlive: false,
        roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
      }
    }
  ]
}

export const modelInferenceRoutes: AppRouteRecord = {
  name: 'ModelInference',
  path: '/model-inference',
  component: '/model-inference/index',
  meta: {
    title: 'menus.modelInference.title',
    icon: 'ri:chat-3-line',
    roles: ['R_SUPER', 'R_ADMIN', 'R_USER']
  }
}

export const systemManagementRoutes: AppRouteRecord = {
  name: 'SystemManagement',
  path: '/system-management',
  component: '/index/index',
  meta: {
    title: 'menus.systemManagement.title',
    icon: 'ri:tools-line',
    roles: ['R_SUPER', 'R_ADMIN']
  },
  children: [
    {
      path: 'users-roles',
      name: 'UsersRoles',
      component: '/system-management/users-roles',
      meta: {
        title: 'menus.systemManagement.usersRoles',
        icon: 'ri:user-settings-line',
        keepAlive: false,
        roles: ['R_SUPER', 'R_ADMIN']
      }
    },
    {
      path: 'advanced-settings',
      name: 'AdvancedSettings',
      component: '/system-management/advanced-settings',
      meta: {
        title: 'menus.systemManagement.advancedSettings',
        icon: 'ri:settings-3-line',
        keepAlive: false,
        roles: ['R_SUPER', 'R_ADMIN']
      }
    }
  ]
}
