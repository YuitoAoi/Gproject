<template>
  <div class="chat-container">
    <!-- 消息列表 -->
    <div ref="messageListRef" class="chat-messages">
      <div v-if="messages.length === 0" class="chat-empty">
        <LfpSvgIcon icon="ri:chat-3-line" class="text-5xl text-g-300" />
        <p class="text-g-400 mt-3">开始一段对话吧</p>
      </div>
      <MessageBubble
        v-for="(msg, index) in messages"
        :key="index"
        :role="msg.role"
        :content="msg.content"
        :is-streaming="streaming && index === messages.length - 1 && msg.role === 'assistant'"
      />
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-bar">
      <div class="input-wrapper">
        <ElSelect
          v-model="selectedModel"
          placeholder="选择模型"
          class="model-select"
          filterable
          :disabled="streaming"
        >
          <ElOption
            v-for="m in modelList"
            :key="m"
            :label="m"
            :value="m"
          />
        </ElSelect>
        <ElInput
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="输入消息，按 Ctrl+Enter 发送..."
          :disabled="streaming || !selectedModel"
          resize="none"
          @keydown.enter.exact.prevent="handleSend"
          @keydown.ctrl.enter.prevent="handleSend"
        />
        <div class="input-actions">
          <ElButton
            size="small"
            text
            :disabled="messages.length === 0"
            @click="handleClear"
          >
            <LfpSvgIcon icon="ri:delete-bin-line" class="mr-1" />清空
          </ElButton>
          <ElButton
            type="primary"
            :loading="streaming"
            :disabled="!inputText.trim() || !selectedModel"
            @click="handleSend"
          >
            <LfpSvgIcon icon="ri:send-plane-fill" class="mr-1" />
            {{ streaming ? '生成中' : '发送' }}
          </ElButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { nextTick, onMounted, ref } from 'vue'
  import { ElMessage } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import MessageBubble from './MessageBubble.vue'
  import { streamChat, type ChatMessage } from '@/utils/sse'
  import { getLlamaFactoryModels, type LlamaFactoryModelsResponse } from '@/api/llamafactory'

  defineOptions({ name: 'ChatContainer' })

  interface Props {
    initialModel?: string
  }

  const props = defineProps<Props>()

  const messageListRef = ref<HTMLElement>()
  const messages = ref<ChatMessage[]>([])
  const inputText = ref('')
  const streaming = ref(false)
  const selectedModel = ref(props.initialModel ?? '')
  const modelList = ref<string[]>([])

  async function loadModels() {
    const resp: LlamaFactoryModelsResponse = await getLlamaFactoryModels()
    if (resp.success && resp.models) {
      modelList.value = resp.models
      if (!selectedModel.value && modelList.value.length > 0) {
        selectedModel.value = modelList.value[0]
      }
    }
  }

  async function handleSend() {
    const text = inputText.value.trim()
    if (!text || !selectedModel.value || streaming.value) return

    inputText.value = ''
    messages.value.push({ role: 'user', content: text })
    messages.value.push({ role: 'assistant', content: '' })
    streaming.value = true
    await scrollToBottom()

    try {
      const userMessages = messages.value
        .filter((m) => m.role !== 'system')
        .map(({ role, content }) => ({ role, content }))
      const assistantIndex = messages.value.length - 1

      for await (const token of streamChat(
        selectedModel.value,
        userMessages,
      )) {
        messages.value[assistantIndex].content += token
        await scrollToBottom()
      }
    } catch (err: any) {
      ElMessage.error(err?.message ?? '对话请求失败')
      messages.value[messages.value.length - 1].content = '抱歉，发生了错误。'
    } finally {
      streaming.value = false
    }
  }

  async function scrollToBottom() {
    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  }

  function handleClear() {
    messages.value = []
  }

  onMounted(() => {
    loadModels()
  })

  defineExpose({ selectedModel })
</script>

<style lang="scss" scoped>
  .chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    background: #fff;
    border-radius: var(--custom-radius, 8px);
    overflow: hidden;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;

    .chat-empty {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    }
  }

  .chat-input-bar {
    border-top: 1px solid var(--lfp-gray-200);
    padding: 12px 16px;
    background: #fff;

    .input-wrapper {
      display: flex;
      flex-direction: column;
      gap: 8px;

      .model-select {
        width: 240px;
      }

      .el-textarea :deep(.el-textarea__inner) {
        font-size: 14px;
        line-height: 1.6;
      }

      .input-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
      }
    }
  }
</style>