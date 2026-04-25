import { AppRouteRecord } from '@/types/router'
import { workbenchRoutes, dataManagementRoutes, modelTrainingRoutes, taskMonitoringRoutes, modelInferenceRoutes } from './workbench'

export const routeModules: AppRouteRecord[] = [
  workbenchRoutes,
  dataManagementRoutes,
  modelTrainingRoutes,
  taskMonitoringRoutes,
  modelInferenceRoutes
]
