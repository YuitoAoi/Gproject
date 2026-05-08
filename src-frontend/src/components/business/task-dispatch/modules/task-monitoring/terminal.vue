<template>
  <div class="terminal">
    <div class="terminal-header">
      <div class="terminal-title">
        <ArtSvgIcon icon="ri:terminal-line" class="text-base text-g-500" />
        <span>终端日志</span>
      </div>
      <div class="terminal-actions">
        <ElButton text size="small" @click="toggleAutoScroll">
          <ArtSvgIcon
            :icon="autoScroll ? 'ri:arrow-down-double-fill' : 'ri:arrow-down-double-line'"
            class="text-sm"
          />
          <span>{{ autoScroll ? '暂停滚动' : '自动滚动' }}</span>
        </ElButton>
        <ElButton text size="small" @click="handleFilterError">
          <ArtSvgIcon icon="ri:filter-line" class="text-sm" />
          <span>过滤 Error</span>
        </ElButton>
        <ElButton text size="small" @click="handleExport">
          <ArtSvgIcon icon="ri:download-line" class="text-sm" />
          <span>导出</span>
        </ElButton>
      </div>
    </div>
    <div ref="terminalBodyRef" class="terminal-body">
      <div v-if="filteredLogs.length === 0" class="terminal-empty">
        <span class="text-g-400">暂无日志</span>
      </div>
      <div
        v-for="(log, index) in filteredLogs"
        :key="index"
        class="terminal-line"
        :class="getLogClass(log)"
      >
        <span class="log-time">{{ log.timestamp }}</span>
        <span class="log-level" :class="log.level.toLowerCase()">[{{ log.level }}]</span>
        <span class="log-message" v-html="highlightLog(log.message)"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { nextTick, onMounted, ref, watch, computed } from 'vue'

  defineOptions({ name: 'Terminal' })

  interface LogEntry {
    timestamp: string
    level: string
    message: string
  }

  interface Props {
    logs?: LogEntry[]
    autoScroll?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    logs: () => [],
    autoScroll: true
  })

  const emit = defineEmits<{
    (e: 'update:autoScroll', val: boolean): void
  }>()

  const terminalBodyRef = ref<HTMLElement>()
  const showErrorOnly = ref(false)

  const filteredLogs = computed(() => {
    if (!showErrorOnly.value) return props.logs
    return props.logs.filter((log) => log.level.toLowerCase().includes('error'))
  })

  const getLogClass = (log: LogEntry) => {
    const level = log.level.toLowerCase()
    if (level.includes('error')) return 'log-error'
    if (level.includes('warn')) return 'log-warn'
    return ''
  }

  const highlightLog = (message: string) => {
    return message
      .replace(/\[INFO\]/g, '<span class="text-info">[INFO]</span>')
      .replace(/\[WARN\]/g, '<span class="text-warning">[WARN]</span>')
      .replace(/\[ERROR\]/g, '<span class="text-danger">[ERROR]</span>')
      .replace(/\{([^}]+)\}/g, '<span class="text-g-600">{$1}</span>')
  }

  const scrollToBottom = () => {
    if (!terminalBodyRef.value || !props.autoScroll) return
    nextTick(() => {
      terminalBodyRef.value!.scrollTop = terminalBodyRef.value!.scrollHeight
    })
  }

  const toggleAutoScroll = () => {
    emit('update:autoScroll', !props.autoScroll)
  }

  const handleFilterError = () => {
    showErrorOnly.value = !showErrorOnly.value
  }

  const handleExport = () => {
    const content = filteredLogs.value
      .map((log) => `[${log.timestamp}] [${log.level}] ${log.message}`)
      .join('\n')
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `terminal-${Date.now()}.log`
    a.click()
    URL.revokeObjectURL(url)
  }

  watch(
    () => props.logs.length,
    () => scrollToBottom()
  )

  onMounted(() => {
    scrollToBottom()
  })
</script>

<style lang="scss" scoped>
  .terminal {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #1a1a2e;
    border-radius: var(--custom-radius, 8px);
    overflow: hidden;

    .terminal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 16px;
      background: #16213e;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      .terminal-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 500;
        color: #e0e0e0;
      }

      .terminal-actions {
        display: flex;
        align-items: center;
        gap: 8px;

        .el-button {
          color: #a0a0a0;
          background: transparent;
          border: none;

          &:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.1);
          }
        }
      }
    }

    .terminal-body {
      flex: 1;
      padding: 12px 16px;
      overflow-y: auto;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 13px;
      line-height: 1.6;
      color: #c0c0c0;

      .terminal-empty {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
      }

      .terminal-line {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 2px 0;

        &.log-error {
          color: #ff6b6b;
          background: rgba(255, 107, 107, 0.1);
          border-radius: 2px;
        }

        &.log-warn {
          color: #ffd93d;
          background: rgba(255, 217, 61, 0.1);
          border-radius: 2px;
        }

        .log-time {
          flex-shrink: 0;
          color: #6b7280;
        }

        .log-level {
          flex-shrink: 0;
          font-weight: 500;

          &.info {
            color: #60a5fa;
          }

          &.warn {
            color: #fbbf24;
          }

          &.error {
            color: #f87171;
          }
        }

        .log-message {
          word-break: break-all;
        }
      }
    }
  }

  :deep(.text-info) {
    color: #60a5fa;
  }

  :deep(.text-warning) {
    color: #fbbf24;
  }

  :deep(.text-danger) {
    color: #f87171;
  }
</style>
