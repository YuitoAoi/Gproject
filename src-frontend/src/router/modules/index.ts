import { AppRouteRecord } from '@/types/router'
import { workbenchRoutes, dataManagementRoutes, modelFactoryRoutes, taskMonitoringRoutes, modelInferenceRoutes, systemManagementRoutes } from './workbench'

export const routeModules: AppRouteRecord[] = [
  workbenchRoutes,
  dataManagementRoutes,
  modelFactoryRoutes,
  taskMonitoringRoutes,
  modelInferenceRoutes,
  systemManagementRoutes
]
