<template>
  <div
    class="message-bubble"
    :class="[`bubble-${role}`, { 'bubble-streaming': isStreaming }]"
  >
    <div class="bubble-avatar">
      <LfpSvgIcon
        v-if="role === 'user'"
        icon="ri:user-line"
        class="text-lg"
      />
      <LfpSvgIcon
        v-else-if="role === 'assistant'"
        icon="ri:android-line"
        class="text-lg"
      />
      <LfpSvgIcon
        v-else
        icon="ri:settings-line"
        class="text-lg"
      />
    </div>
    <div class="bubble-content">
      <div v-if="role !== 'user'" class="bubble-header">
        <span class="bubble-role">{{ roleName }}</span>
        <div v-if="role === 'assistant'" class="bubble-actions">
          <ElTooltip content="复制" placement="top">
            <button class="action-btn" @click="copyContent">
              <LfpSvgIcon icon="ri:clipboard-line" class="text-sm" />
            </button>
          </ElTooltip>
        </div>
      </div>
      <div class="bubble-body" :class="{ 'content-code': hasCodeBlock }">
        <div
          v-if="renderedContent"
          class="markdown-body"
          v-html="renderedContent"
        ></div>
        <span v-else-if="!content" class="bubble-placeholder">
          <LfpSvgIcon
            v-if="role === 'assistant' && isStreaming"
            icon="ri:loader-4-line"
            class="animate-spin text-sm"
          />
          <span v-if="role === 'assistant' && isStreaming"> 生成中...</span>
        </span>
        <span v-else class="bubble-text">{{ content }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'

  defineOptions({ name: 'MessageBubble' })

  interface Props {
    role: 'system' | 'user' | 'assistant'
    content: string
    isStreaming?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    isStreaming: false,
  })

  const roleName = computed(() => {
    const map: Record<string, string> = {
      assistant: 'AI 助手',
      system: '系统',
      user: '我',
    }
    return map[props.role] ?? props.role
  })

  const hasCodeBlock = computed(() => {
    return props.content.includes('```') || props.content.includes('`')
  })

  /** 简单 Markdown 渲染：代码块 + 行内代码 + 粗体 + 换行 */
  const renderedContent = computed(() => {
    if (!props.content) return ''
    let html = props.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    // 代码块
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_m, _lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`
    })
    // 行内代码
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
    // 粗体
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // 换行
    html = html.replace(/\n/g, '<br>')
    return html
  })

  async function copyContent() {
    try {
      await navigator.clipboard.writeText(props.content)
      ElMessage.success('已复制')
    } catch {
      ElMessage.error('复制失败')
    }
  }
</script>

<style lang="scss" scoped>
  .message-bubble {
    display: flex;
    gap: 12px;
    max-width: 80%;

    &.bubble-user {
      flex-direction: row-reverse;
      margin-left: auto;

      .bubble-content {
        background: var(--el-color-primary-light-8);
        border-radius: 16px 4px 16px 16px;
      }
    }

    &.bubble-assistant {
      margin-right: auto;

      .bubble-content {
        background: #f0f2f5;
        border-radius: 4px 16px 16px 16px;
      }
    }

    &.bubble-system {
      justify-content: center;
      margin: 0 auto;

      .bubble-content {
        background: #fffbeb;
        border-radius: 8px;
        padding: 8px 16px;
      }

      .bubble-body {
        font-size: 12px;
        color: var(--lfp-gray-500);
      }
    }
  }

  .bubble-avatar {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--el-color-primary-light-8);
    color: var(--lfp-gray-500);
    align-self: flex-start;
  }

  .bubble-content {
    flex: 1;
    min-width: 0;
    padding: 10px 14px;

    &.content-code {
      background: #1e1e1e;
      padding: 12px 16px;

      :deep(.markdown-body) {
        color: #d4d4d4;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
      }

      :deep(pre) {
        background: #2d2d2d;
        border-radius: 6px;
        padding: 12px;
        overflow-x: auto;
        margin: 6px 0;
      }

      :deep(code) {
        color: #ce9178;
      }

      :deep(strong) {
        color: #dcdcaa;
      }
    }
  }

  .bubble-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;

    .bubble-role {
      font-size: 11px;
      font-weight: 600;
      color: var(--lfp-gray-400);
      text-transform: uppercase;
    }

    .bubble-actions {
      display: flex;
      gap: 4px;

      .action-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border: none;
        background: transparent;
        color: var(--lfp-gray-400);
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.15s;

        &:hover {
          background: rgba(0, 0, 0, 0.08);
          color: var(--lfp-gray-600);
        }
      }
    }
  }

  .bubble-body {
    font-size: 14px;
    line-height: 1.7;
    color: var(--lfp-gray-800);
    word-break: break-word;

    :deep(.markdown-body) {
      font-size: 14px;
      line-height: 1.7;
      color: var(--lfp-gray-800);

      pre {
        margin: 8px 0;
      }

      strong {
        font-weight: 600;
      }
    }

    .bubble-placeholder {
      color: var(--lfp-gray-400);
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>