<template>
  <div class="model-registry-page">
    <!-- ========== 页头区域 ========== -->
    <div class="page-header mb-5">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="page-header__title">模型仓库</h1>
          <p class="page-header__subtitle">管理已注册的基础模型与微调产物，一键部署推理服务。</p>
        </div>
        <ElButton class="page-header__button" size="large" @click="handleRefresh" :loading="loading">
          <LfpSvgIcon icon="ri:refresh-line" class="mr-1" />
          刷新模型列表
        </ElButton>
      </div>
    </div>

    <!-- ========== 统计面板（可点击滚动） ========== -->
    <div class="stats-panel grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
      <button class="stat-card-btn" @click="scrollToSection('registry')">
        <div class="lfp-card p-5 relative">
          <p class="text-sm text-g-500">已注册模型</p>
          <div class="text-2xl font-medium mt-2">{{ models.length }}</div>
          <div class="size-10 rounded-lg flex-cc bg-theme/10 absolute top-4 right-4">
            <LfpSvgIcon icon="ri:brain-line" class="text-lg text-theme" />
          </div>
        </div>
      </button>
      <button class="stat-card-btn" @click="scrollToSection('finetuned')">
        <div class="lfp-card p-5 relative">
          <p class="text-sm text-g-500">微调产物</p>
          <div class="text-2xl font-medium mt-2">{{ fineTunedCount }}</div>
          <div class="size-10 rounded-lg flex-cc bg-success/10 absolute top-4 right-4">
            <LfpSvgIcon icon="ri:flashlight-line" class="text-lg text-success" />
          </div>
        </div>
      </button>
      <button class="stat-card-btn" @click="scrollToSection('online')">
        <div class="lfp-card p-5 relative">
          <p class="text-sm text-g-500">在线服务</p>
          <div class="text-2xl font-medium mt-2">
            <span class="text-success">{{ onlineCount }}</span>
            <span class="text-g-400 text-base"> / {{ models.length }}</span>
          </div>
          <div class="size-10 rounded-lg flex-cc bg-primary/10 absolute top-4 right-4">
            <LfpSvgIcon icon="ri:server-line" class="text-lg text-primary" />
          </div>
        </div>
      </button>
    </div>

    <!-- ========== 工具栏 ========== -->
    <div id="registry" class="lfp-card p-4 mb-5">
      <div class="flex items-center gap-3 flex-wrap">
        <ElInput
          v-model="searchKeyword"
          placeholder="搜索模型名称..."
          class="!w-72"
          clearable
        >
          <template #prefix>
            <LfpSvgIcon icon="ri:search-line" class="text-g-400" />
          </template>
        </ElInput>
        <ElSelect v-model="filterType" placeholder="模型类型" class="!w-36" clearable>
          <ElOption value="base" label="基础模型" />
          <ElOption value="finetuned" label="微调产物" />
        </ElSelect>
        <div class="flex-1"></div>
        <span class="text-sm text-g-500">
          共 <span class="font-medium text-g-700">{{ filteredModels.length }}</span> 个模型
        </span>
      </div>
    </div>

    <!-- ========== 加载状态 ========== -->
    <div v-if="loading" class="model-grid">
      <div v-for="i in 6" :key="i" class="lfp-card p-5 skeleton-card">
        <div class="skeleton-line w-3/5 mb-3"></div>
        <div class="skeleton-line w-2/5 mb-4"></div>
        <div class="flex gap-2">
          <div class="skeleton-tag w-12"></div>
          <div class="skeleton-tag w-16"></div>
        </div>
      </div>
    </div>

    <!-- ========== 模型卡片网格 ========== -->
    <div v-else-if="filteredModels.length > 0" class="model-grid">
      <div
        v-for="model in filteredModels"
        :key="model.id"
        class="model-card lfp-card"
        @click="handleOpenDetail(model)"
      >
        <!-- 卡片头部 -->
        <div class="model-card__header">
          <div class="model-card__icon" :class="model.isFineTuned ? 'bg-success/10' : 'bg-primary/10'">
            <LfpSvgIcon
              :icon="model.isFineTuned ? 'ri:flashlight-line' : 'ri:brain-line'"
              :class="model.isFineTuned ? 'text-success' : 'text-primary'"
              class="text-xl"
            />
          </div>
          <div class="model-card__title-area">
            <span class="model-card__name" :title="model.id">{{ model.displayName }}</span>
            <span class="model-card__org text-xs text-g-400">{{ model.org }}</span>
          </div>
          <ElTag
            :type="model.isFineTuned ? 'success' : 'primary'"
            size="small"
            effect="plain"
            class="flex-shrink-0"
          >
            {{ model.isFineTuned ? '微调' : '基础' }}
          </ElTag>
        </div>

        <!-- 卡片元信息 -->
        <div class="model-card__meta">
          <div class="meta-item" v-if="model.paramSize">
            <LfpSvgIcon icon="ri:cpu-line" class="text-g-400" />
            <span>{{ model.paramSize }}</span>
          </div>
          <div class="meta-item">
            <LfpSvgIcon icon="ri:server-line" class="text-g-400" />
            <span :class="model.online ? 'text-success' : 'text-g-400'">
              {{ model.online ? '在线' : '离线' }}
            </span>
          </div>
        </div>

        <!-- 底部操作 -->
        <div class="model-card__actions">
          <ElButton v-if="model.online" size="small" type="primary" @click.stop="enterChat(model)">
            <LfpSvgIcon icon="ri:chat-3-line" class="mr-1" />进入对话
          </ElButton>
          <ElButton v-else-if="model.isFineTuned" size="small" type="success" @click.stop="startInference(model)">
            <LfpSvgIcon icon="ri:play-line" class="mr-1" />开启推理测试
          </ElButton>
          <ElButton v-else size="small" text type="primary" @click.stop="handleChat(model)">
            <LfpSvgIcon icon="ri:chat-3-line" class="mr-1" />对话测试
          </ElButton>
          <ElButton size="small" text @click.stop="handleOpenDetail(model)">
            <LfpSvgIcon icon="ri:information-line" class="mr-1" />详情
          </ElButton>
        </div>
      </div>
    </div>

    <!-- ========== 空状态 ========== -->
    <div v-else class="lfp-card p-14 text-center">
      <LfpSvgIcon icon="ri:inbox-line" class="text-5xl text-g-300 mb-4" />
      <p class="text-g-500 mb-1">
        {{ searchKeyword || filterType ? '未找到匹配的模型' : '暂无已注册模型' }}
      </p>
      <p class="text-xs text-g-400 mt-2">
        <template v-if="searchKeyword || filterType">尝试修改搜索条件</template>
        <template v-else>请确保 LlamaFactory 推理服务已启动</template>
      </p>
    </div>

    <!-- ========== 模型详情抽屉 ========== -->
    <ModelDrawer
      v-model:visible="drawerVisible"
      :model="selectedModel"
    />
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import ModelDrawer from './modules/model-drawer.vue'
  import { getLlamaFactoryModels } from '@/api/llamafactory'

  defineOptions({ name: 'ModelRegistryPage' })

  const router = useRouter()

  interface ModelItem {
    id: string
    displayName: string
    org: string
    paramSize: string
    isFineTuned: boolean
    online: boolean
  }

  const models = ref<ModelItem[]>([])
  const loading = ref(false)
  const searchKeyword = ref('')
  const filterType = ref<string>('')
  const drawerVisible = ref(false)
  const selectedModel = ref<ModelItem | null>(null)

  const fineTunedCount = computed(() => models.value.filter(m => m.isFineTuned).length)
  const onlineCount = computed(() => models.value.filter(m => m.online).length)

  const filteredModels = computed(() => {
    let result = models.value
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.trim().toLowerCase()
      result = result.filter(m => m.id.toLowerCase().includes(kw) || m.displayName.toLowerCase().includes(kw))
    }
    if (filterType.value === 'base') {
      result = result.filter(m => !m.isFineTuned)
    } else if (filterType.value === 'finetuned') {
      result = result.filter(m => m.isFineTuned)
    }
    return result
  })

  /** 从模型 id 解析展示信息 */
  function parseModelId(id: string): ModelItem {
    const parts = id.split('/')
    const org = parts.length > 1 ? parts[0] : ''
    const name = parts.length > 1 ? parts.slice(1).join('/') : id

    const sizeMatch = name.match(/(\d+\.?\d*)[Bb]/)
    const paramSize = sizeMatch ? sizeMatch[0].toUpperCase() : ''

    const fineTunePatterns = ['lora', 'adapter', 'merged', 'finetuned', 'ft-', 'sft']
    const isFineTuned = fineTunePatterns.some(p => id.toLowerCase().includes(p))

    return {
      id,
      displayName: name,
      org,
      paramSize,
      isFineTuned,
      online: true,
    }
  }

  async function fetchModels() {
    loading.value = true
    try {
      const resp = await getLlamaFactoryModels()
      if (resp.success && resp.models) {
        models.value = resp.models.map(parseModelId)
      } else {
        models.value = []
        if (resp.error) {
          ElMessage.warning('获取模型列表失败: ' + resp.error)
        }
      }
    } catch (err: any) {
      console.error('[ModelRegistry] 获取模型列表失败:', err)
      models.value = []
      ElMessage.error('无法连接到模型服务')
    } finally {
      loading.value = false
    }
  }

  function handleRefresh() {
    fetchModels()
  }

  function handleOpenDetail(model: ModelItem) {
    selectedModel.value = model
    drawerVisible.value = true
  }

  function handleChat(model: ModelItem) {
    router.push({ path: '/model-inference', query: { model: model.id } })
  }

  function scrollToSection(section: 'registry' | 'finetuned' | 'online') {
    if (section === 'finetuned') {
      filterType.value = 'finetuned'
    } else if (section === 'online') {
      filterType.value = ''
    }
    const el = document.getElementById('registry')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  function enterChat(model: ModelItem) {
    router.push({ path: '/model-inference', query: { model: model.id } })
  }

  function startInference(model: ModelItem) {
    router.push({ path: '/model-inference', query: { model: model.id } })
  }

  onMounted(() => {
    fetchModels()
  })
</script>

<style lang="scss" scoped>
  .model-registry-page {
    padding: 16px 20px;
  }

  .page-header {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 20px 2rem;
    overflow: hidden;
    color: white;
    background-color: color-mix(in srgb, var(--el-color-primary) 60%, transparent);
    border-radius: calc(var(--custom-radius, 8px) + 2px);

    &::after {
      position: absolute;
      right: -10%;
      bottom: -20%;
      width: 60%;
      height: 140%;
      content: '';
      background: rgb(255 255 255 / 12%);
      border-radius: 30%;
      transform: rotate(-20deg);
    }

    &__title {
      position: relative;
      z-index: 1;
      margin: 0 0 0.25rem;
      font-size: 1.5rem;
      font-weight: 700;
      color: #fff;
    }

    &__subtitle {
      position: relative;
      z-index: 1;
      margin: 0;
      font-size: 0.9rem;
      opacity: 0.9;
      color: #fff;
    }

    &__button {
      position: relative;
      z-index: 1;
      background: rgba(255, 255, 255, 0.2) !important;
      border-color: rgba(255, 255, 255, 0.4) !important;
      color: #fff !important;
      backdrop-filter: blur(4px);

      &:hover {
        background: rgba(255, 255, 255, 0.3) !important;
      }
    }
  }

  .stats-panel {
    .stat-card-btn {
      display: block;
      width: 100%;
      padding: 0;
      border: none;
      background: transparent;
      cursor: pointer;
      text-align: left;

      .lfp-card {
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
        border: 1px solid transparent;
      }

      &:hover .lfp-card {
        border-color: var(--el-color-primary-light-5);
        box-shadow: 0 4px 14px rgba(64, 158, 255, 0.12);
        transform: translateY(-2px);
      }
    }
  }

  .model-grid {
    display: grid;
    grid-template-columns: repeat(1, 1fr);
    gap: 16px;

    @media (min-width: 640px) {
      grid-template-columns: repeat(2, 1fr);
    }

    @media (min-width: 1024px) {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  .model-card {
    padding: 20px;
    cursor: pointer;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    border: 1px solid transparent;

    &:hover {
      border-color: var(--el-color-primary-light-5);
      box-shadow: 0 4px 14px rgba(64, 158, 255, 0.12);
      transform: translateY(-2px);
    }

    &__header {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 16px;
    }

    &__icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    &__title-area {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    &__name {
      font-size: 14px;
      font-weight: 600;
      color: var(--lfp-gray-800);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    &__meta {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 16px;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: var(--lfp-gray-600);
      }
    }

    &__actions {
      display: flex;
      align-items: center;
      gap: 4px;
      padding-top: 12px;
      border-top: 1px solid var(--lfp-gray-200);
    }
  }

  .skeleton-card {
    cursor: default;
    pointer-events: none;
  }

  .skeleton-line {
    height: 13px;
    background: var(--lfp-gray-200, #ebeef5);
    border-radius: 4px;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  .skeleton-tag {
    height: 20px;
    background: var(--lfp-gray-200, #ebeef5);
    border-radius: 4px;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  @keyframes shimmer {
    0% { opacity: 1; }
    50% { opacity: 0.4; }
    100% { opacity: 1; }
  }
</style>
