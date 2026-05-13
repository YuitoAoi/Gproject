/**
 * 路由配置
 *
 * 所有路由静态定义，组件使用懒加载
 * 菜单数据直接从路由 meta 中提取
 */
import type { RouteRecordRaw } from 'vue-router'

/** 默认首页路径（被根路由 redirect、路由守卫、侧边栏共用） */
export const HOME_PATH = '/workbench/dashboard'

/** 主布局组件 */
const Layout = () => import('@/views/index/index.vue')

/** 认证相关页面（无需登录） */
export const publicRoutes: RouteRecordRaw[] = [
  // 根路径重定向到首页
  {
    path: '/',
    redirect: HOME_PATH
  },
  {
    path: '/auth/login',
    name: 'Login',
    component: () => import('@/views/auth/login/index.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/auth/register',
    name: 'Register',
    component: () => import('@/views/auth/register/index.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/auth/forget-password',
    name: 'ForgetPassword',
    component: () => import('@/views/auth/forget-password/index.vue'),
    meta: { title: '忘记密码' }
  },
  {
    path: '/403',
    name: 'Exception403',
    component: () => import('@/views/exception/403/index.vue'),
    meta: { title: '403' }
  },
  {
    path: '/500',
    name: 'Exception500',
    component: () => import('@/views/exception/500/index.vue'),
    meta: { title: '500' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'Exception404',
    component: () => import('@/views/exception/404/index.vue'),
    meta: { title: '404' }
  }
]

/** 业务路由（需要登录，使用 Layout 包裹） */
export const businessRoutes: RouteRecordRaw[] = [
  {
    path: '/workbench',
    component: Layout,
    meta: { title: '工作台', icon: 'ri:settings-4-line' },
    redirect: '/workbench/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/workbench/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'ri:home-smile-2-line' }
      },
      {
        path: 'compute-storage',
        name: 'ComputeStorage',
        component: () => import('@/views/workbench/compute-storage/index.vue'),
        meta: { title: '算力存储', icon: 'ri:computer-line' }
      },
      {
        path: 'task-dispatch',
        name: 'TaskDispatch',
        component: () => import('@/views/workbench/task-dispatch/index.vue'),
        meta: { title: '任务调度中心', icon: 'ri:timer-flash-line' }
      },
      // 隐藏子路由：通过编程导航访问，不出现在侧边栏
      {
        path: 'task-monitoring/:id',
        name: 'TaskMonitoringDetail',
        component: () => import('@/views/task-monitoring/index.vue'),
        meta: { title: '任务监控详情', hidden: true }
      },
      {
        path: 'cleaning-monitor/:id',
        name: 'CleaningMonitoringDetail',
        component: () => import('@/views/cleaning-monitor/index.vue'),
        meta: { title: '清洗监控详情', hidden: true }
      }
    ]
  },
  {
    path: '/data-management',
    component: Layout,
    meta: { title: '数据管理', icon: 'ri:folder-open-line' },
    redirect: '/data-management/dataset-hub',
    children: [
      {
        path: 'dataset-hub',
        name: 'DatasetHub',
        component: () => import('@/views/data-management/dataset-hub/index.vue'),
        meta: { title: '数据集中心', icon: 'ri:database-2-line' }
      },
      {
        path: 'data-processing',
        name: 'DataProcessing',
        component: () => import('@/views/data-management/data-processing/index.vue'),
        meta: { title: '数据处理', icon: 'ri:refresh-line' }
      }
    ]
  },
  {
    path: '/model-factory',
    component: Layout,
    meta: { title: '模型工厂', icon: 'ri:cpu-line' },
    redirect: '/model-factory/new-training',
    children: [
      {
        path: 'new-training',
        name: 'NewTraining',
        component: () => import('@/views/model-factory/new-training/index.vue'),
        meta: { title: '新建训练', icon: 'ri:rocket-line' }
      },
      {
        path: 'model-registry',
        name: 'ModelRegistry',
        component: () => import('@/views/model-factory/model-registry/index.vue'),
        meta: { title: '模型仓库', icon: 'ri:archive-line' }
      }
    ]
  },
  {
    path: '/model-inference',
    component: Layout,
    meta: { title: '模型推理', icon: 'ri:chat-3-line' },
    children: [
      {
        path: '',
        name: 'ModelInference',
        component: () => import('@/views/model-inference/index.vue'),
        meta: { title: '模型推理', icon: 'ri:chat-3-line' }
      }
    ]
  },
  {
    path: '/system-management',
    component: Layout,
    meta: { title: '系统管理', icon: 'ri:tools-line', roles: ['R_ADMIN'] },
    redirect: '/system-management/users-roles',
    children: [
      {
        path: 'users-roles',
        name: 'UsersRoles',
        component: () => import('@/views/system-management/users-roles/index.vue'),
        meta: { title: '用户与角色', icon: 'ri:user-settings-line', roles: ['R_ADMIN'] }
      },
      {
        path: 'advanced-settings',
        name: 'AdvancedSettings',
        component: () => import('@/views/system-management/advanced-settings/index.vue'),
        meta: { title: '高级设置', icon: 'ri:settings-3-line', roles: ['R_ADMIN'] }
      }
    ]
  }
]
