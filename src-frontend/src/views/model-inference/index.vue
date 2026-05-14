<template>
  <div class="inference-page">
    <!-- 无推理任务：空状态 -->
    <div v-if="!hasModel" class="inference-empty lfp-card">
      <LfpSvgIcon icon="ri:chat-3-line" class="text-6xl text-g-300 mb-4" />
      <h2 class="text-xl font-medium mb-2">暂无推理任务</h2>
      <p class="text-g-500 mb-5">请先从模型仓库选择一个模型，开启对话测试</p>
      <ElButton type="primary" @click="goToModelRegistry">
        <LfpSvgIcon icon="ri:archive-line" class="mr-1" />
        前往模型仓库
      </ElButton>
    </div>

    <!-- 有推理任务：对话沙盒 -->
    <div v-else class="inference-chat">
      <!-- 顶部工具栏 -->
      <div class="chat-toolbar">
        <div class="toolbar-left">
          <LfpSvgIcon icon="ri:chat-3-line" class="text-lg text-primary mr-2" />
          <span class="toolbar-title">推理对话</span>
          <ElTag size="small" type="success" effect="plain" class="ml-2">
            {{ route.query.model }}
          </ElTag>
        </div>
        <div class="toolbar-right">
          <ElButton size="small" text @click="goToModelRegistry">
            <LfpSvgIcon icon="ri:arrow-left-s-line" class="mr-1" />
            切换模型
          </ElButton>
        </div>
      </div>
      <!-- 对话容器 -->
      <ChatContainer :initial-model="route.query.model as string" class="chat-area" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import ChatContainer from '@/components/business/chat/ChatContainer.vue'

  defineOptions({ name: 'ModelInferencePage' })

  const route = useRoute()
  const router = useRouter()

  /** 当前是否有选中的模型（来自路由参数） */
  const hasModel = computed(() => {
    return !!route.query.model
  })

  function goToModelRegistry() {
    router.push('/model-factory/model-registry')
  }
</script>

<style lang="scss" scoped>
  .inference-page {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 16px 20px;
    min-height: 0;
  }

  .inference-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
  }

  .inference-chat {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    gap: 12px;

    .chat-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 16px;
      background: #fff;
      border-radius: var(--custom-radius, 8px);
      border: 1px solid var(--lfp-gray-200);

      .toolbar-left {
        display: flex;
        align-items: center;
      }

      .toolbar-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--lfp-gray-700);
      }
    }

    .chat-area {
      flex: 1;
      min-height: 0;
    }
  }
</style>