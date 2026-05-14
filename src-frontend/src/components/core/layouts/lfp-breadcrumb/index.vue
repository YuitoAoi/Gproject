<!-- 面包屑导航 -->
<template>
  <nav class="ml-2.5 max-lg:!hidden" aria-label="breadcrumb">
    <ul class="flex-c h-full">
      <li
        v-for="(item, index) in items"
        :key="item.path"
        class="box-border flex-c h-7 text-sm leading-7"
      >
        <div
          :class="
            !isLast(index)
              ? 'c-p py-1 rounded tad-200 hover:bg-active-color hover:[&_span]:text-g-600'
              : ''
          "
          @click="!isLast(index) && router.push(item.path)"
        >
          <span
            class="block max-w-46 overflow-hidden text-ellipsis whitespace-nowrap px-1.5 text-sm text-g-600 dark:text-g-800"
            >{{ item.title }}</span
          >
        </div>
        <div
          v-if="!isLast(index)"
          class="mx-1 text-sm not-italic text-g-500"
          aria-hidden="true"
        >
          /
        </div>
      </li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useRouter, useRoute } from 'vue-router'

  defineOptions({ name: 'LfpBreadcrumb' })

  const route = useRoute()
  const router = useRouter()

  const items = computed(() =>
    route.matched
      .filter((r) => r.meta?.title && !r.meta?.hidden)
      .map((r) => ({ path: r.path, title: r.meta!.title as string }))
  )

  const isLast = (i: number) => i === items.value.length - 1
</script>
