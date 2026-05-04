/**
 * 任务进度状态管理
 *
 * 管理Celery异步任务（上传、清洗、转换）的实时进度
 * 通过WebSocket实时推送进度更新
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface TaskProgress {
  taskId: string
  current: number
  total: number
  percentage: number
  phase: string
  status: 'pending' | 'running' | 'success' | 'failure'
  message: string
  createdAt: string
  updatedAt: string
}

export const useTaskStore = defineStore(
  'taskStore',
  () => {
    // 所有任务
    const tasks = ref<Map<string, TaskProgress>>(new Map())

    // 排序后的任务列表
    const taskList = computed(() => {
      return Array.from(tasks.value.values()).sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      )
    })

    // 进行中的任务
    const runningTasks = computed(() =>
      taskList.value.filter((t) => t.status === 'running' || t.status === 'pending')
    )

    // 已完成的任务
    const completedTasks = computed(() =>
      taskList.value.filter((t) => t.status === 'success')
    )

    // 失败的任务
    const failedTasks = computed(() =>
      taskList.value.filter((t) => t.status === 'failure')
    )

    // 更新或创建任务进度
    function updateTask(taskId: string, updates: Partial<TaskProgress>) {
      const existing = tasks.value.get(taskId)
      if (existing) {
        Object.assign(existing, {
          ...updates,
          updatedAt: new Date().toISOString()
        })
        // 触发响应式更新
        tasks.value = new Map(tasks.value)
      } else {
        tasks.value.set(taskId, {
          taskId,
          current: 0,
          total: 100,
          percentage: 0,
          phase: '',
          status: 'pending',
          message: '',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          ...updates
        })
        tasks.value = new Map(tasks.value)
      }
    }

    // 获取指定任务
    function getTask(taskId: string): TaskProgress | undefined {
      return tasks.value.get(taskId)
    }

    // 移除指定任务
    function removeTask(taskId: string) {
      tasks.value.delete(taskId)
      tasks.value = new Map(tasks.value)
    }

    // 清空已完成的任务
    function clearCompleted() {
      const toRemove: string[] = []
      tasks.value.forEach((task, key) => {
        if (task.status === 'success' || task.status === 'failure') {
          toRemove.push(key)
        }
      })
      toRemove.forEach((key) => tasks.value.delete(key))
      tasks.value = new Map(tasks.value)
    }

    return {
      tasks,
      taskList,
      runningTasks,
      completedTasks,
      failedTasks,
      updateTask,
      getTask,
      removeTask,
      clearCompleted
    }
  }
)
