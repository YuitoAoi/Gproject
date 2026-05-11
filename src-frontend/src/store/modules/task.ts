/**
 * 任务进度状态管理（WebSocket 实时缓存）
 *
 * 仅用于监控页 WebSocket 推送时的本地 UI 缓存。
 * 任务队列的权威数据源是后端 MySQL tasks 表，通过 GET /tasks API 查询。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TaskStatus, TaskType } from '@/utils/task'

export interface TaskRecord {
  taskId: string
  taskName: string
  taskType: TaskType
  current: number
  total: number
  percentage: number
  phase: string
  status: TaskStatus
  message: string
  logPath?: string
  createdAt: string
  updatedAt: string
}

export const useTaskStore = defineStore('taskStore', () => {
  const tasks = ref<Map<string, TaskRecord>>(new Map())

  const taskList = computed(() => {
    return Array.from(tasks.value.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    )
  })

  const runningTasks = computed(() =>
    taskList.value.filter((t) => t.status === 'running' || t.status === 'pending')
  )

  const pendingTasks = computed(() => taskList.value.filter((t) => t.status === 'pending'))

  const completedTasks = computed(() => taskList.value.filter((t) => t.status === 'done'))

  const failedTasks = computed(() => taskList.value.filter((t) => t.status === 'failed'))

  function updateTask(taskId: string, updates: Partial<TaskRecord>) {
    const existing = tasks.value.get(taskId)
    const now = new Date().toISOString()
    if (existing) {
      Object.assign(existing, {
        ...updates,
        updatedAt: now
      })
      tasks.value = new Map(tasks.value)
    } else {
      tasks.value.set(taskId, {
        taskId,
        taskName: taskId.slice(0, 8),
        taskType: 'cleaning',
        current: 0,
        total: 100,
        percentage: 0,
        phase: '',
        status: 'pending' as TaskStatus,
        message: '',
        createdAt: now,
        updatedAt: now,
        ...updates
      })
      tasks.value = new Map(tasks.value)
    }
  }

  function getTask(taskId: string): TaskRecord | undefined {
    return tasks.value.get(taskId)
  }

  function removeTask(taskId: string) {
    tasks.value.delete(taskId)
    tasks.value = new Map(tasks.value)
  }

  function clearCompleted() {
    const toRemove: string[] = []
    tasks.value.forEach((task, key) => {
      if (task.status === 'done' || task.status === 'failed' || task.status === 'cancelled') {
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
    pendingTasks,
    completedTasks,
    failedTasks,
    updateTask,
    getTask,
    removeTask,
    clearCompleted
  }
})
