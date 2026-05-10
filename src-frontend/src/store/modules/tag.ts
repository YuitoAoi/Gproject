/**
 * 标签状态管理模块
 *
 * 提供数据集标签的集中状态管理
 *
 * ## 主要功能
 *
 * - 标签列表统一管理
 * - 标签数据获取与缓存
 * - 标签创建后自动更新列表
 * - 多组件间标签状态共享
 *
 * ## 使用场景
 *
 * - 数据集管理页面标签展示
 * - 数据集编辑抽屉标签选择
 * - 标签筛选器
 *
 * ## 数据结构
 *
 * - tags: TagInfo[] 标签列表
 * - loading: boolean 加载状态
 *
 * @module store/modules/tag
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTags, createTag, deleteTag } from '@/api/dataset'

export interface TagInfo {
  tag_id: number
  tag_name: string
  tag_color: string
  tag_desc: string
  tag_created_at: string
}

export const useTagStore = defineStore(
  'tagStore',
  () => {
    const tags = ref<TagInfo[]>([])
    const loading = ref(false)

    async function fetchTags() {
      loading.value = true
      const res = await getTags()
      if (res.success) {
        tags.value = res.tags
      }
      loading.value = false
    }

    async function addTag(name: string, color: string, desc: string = '') {
      const res = await createTag(name, color, desc)
      if (res.success) {
        await fetchTags()
      }
      return res
    }

    async function removeTag(tagId: number) {
      const res = await deleteTag(tagId)
      if (res.success) {
        await fetchTags()
      }
      return res
    }

    return {
      tags,
      loading,
      fetchTags,
      addTag,
      removeTag
    }
  },
  {
    persist: {
      key: 'tag',
      storage: localStorage
    }
  }
)
