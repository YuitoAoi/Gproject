<template>
  <div class="task-dispatch-page">
    <!-- ========== 模块一：页头区域 ========== -->
    <div class="page-header mb-5">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="page-header__title">任务调度中心</h1>
          <p class="page-header__subtitle"
            >这里是您的所有任务流水管理线，可对所有任务进度进行查看与调整。</p
          >
        </div>
      </div>
    </div>

    <!-- ========== 模块二：全局任务大盘 ========== -->
    <TaskDashboard class="mb-5" />

    <!-- ========== 模块三：任务控制台 ========== -->
    <TaskConsole />
  </div>
</template>

<script setup lang="ts">
  import TaskDashboard from '@/components/business/task-dispatch/modules/task-dashboard.vue'
  import TaskConsole from '@/components/business/task-dispatch/modules/task-console.vue'

  defineOptions({ name: 'TaskDispatchPage' })
</script>

<style lang="scss" scoped>
  .task-dispatch-page {
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
  }
</style>
