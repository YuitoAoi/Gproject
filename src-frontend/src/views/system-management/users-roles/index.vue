<template>
  <div class="p-6">
    <!-- 页头 -->
    <div class="page-header mb-5">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-g-800">用户管理</h1>
          <p class="text-sm text-g-500 mt-1">管理系统中的所有用户账户，包括启用/禁用、角色分配等操作。</p>
        </div>
      </div>
    </div>

    <!-- 搜索栏 + 表格 -->
    <ElCard shadow="never" class="!border-g-200">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div class="flex items-center gap-3 flex-wrap">
          <ElInput
            v-model="(searchParams as any).keyword"
            placeholder="搜索用户名或邮箱..."
            class="!w-64"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <span class="ri:search-line text-g-400"></span>
            </template>
          </ElInput>
          <ElButton type="primary" @click="handleSearch">
            <span class="ri:search-line mr-1"></span>查询
          </ElButton>
          <ElButton @click="handleReset">
            <span class="ri:refresh-line mr-1"></span>重置
          </ElButton>
        </div>
        <div class="text-sm text-g-500">
          共 <span class="font-medium text-g-700">{{ pagination.total }}</span> 位用户
        </div>
      </div>

      <!-- 表格 -->
      <LfpTable
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        empty-height="300px"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      >
      </LfpTable>
    </ElCard>

    <!-- 编辑弹窗 -->
    <ElDialog v-model="editVisible" title="用户操作" width="440px" :close-on-click-modal="false">
      <div v-if="editUser" class="space-y-4">
        <div class="flex items-center gap-3 p-3 bg-g-50 rounded-lg">
          <div>
            <p class="font-medium text-g-800">{{ editUser.name }}</p>
            <p class="text-xs text-g-500">{{ editUser.email }}</p>
          </div>
        </div>

        <ElForm label-width="80px">
          <ElFormItem label="账户状态">
            <ElSwitch
              v-model="editForm.is_active"
              active-text="启用"
              inactive-text="禁用"
              :disabled="editUser.id === 0"
            />
          </ElFormItem>
          <ElFormItem label="管理员">
            <ElSwitch
              v-model="editForm.is_admin"
              active-text="是"
              inactive-text="否"
              :disabled="editUser.id === 0"
            />
          </ElFormItem>
        </ElForm>
      </div>
      <template #footer>
        <ElButton @click="editVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="editLoading" @click="handleEditSubmit">保存</ElButton>
      </template>
    </ElDialog>

    <!-- 重置密码弹窗 -->
    <ElDialog v-model="resetPwdVisible" title="重置密码" width="400px" :close-on-click-modal="false">
      <p class="text-sm text-g-600 mb-4">
        为用户 <span class="font-medium">{{ resetPwdUser?.name }}</span> 设置新密码：
      </p>
      <ElForm ref="resetPwdFormRef" :model="resetPwdForm" :rules="resetPwdRules">
        <ElFormItem prop="new_password">
          <ElInput
            v-model="resetPwdForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码（至少8位）"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="resetPwdVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="resetPwdLoading" @click="handleResetPassword">确认重置</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, h } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { useTable } from '@/hooks/core/useTable'
  import LfpButtonTable from '@/components/core/forms/lfp-button-table/index.vue'
  import {
    fetchGetUserList,
    fetchToggleUserActive,
    fetchSetUserAdmin,
    fetchResetUserPassword,
    fetchDeleteUser
  } from '@/api/system-manage'

  defineOptions({ name: 'UsersRolesPage' })

  const {
    columns,
    data,
    loading,
    pagination,
    searchParams,
    handleSizeChange,
    handleCurrentChange,
    refreshData,
    resetSearchParams
  } = useTable({
    core: {
      apiFn: fetchGetUserList,
      apiParams: { page: 1, size: 10, keyword: '' },
      immediate: true,
      paginationKey: { current: 'page', size: 'size' },
      columnsFactory: () => [
        { type: 'index' as const, width: 50, label: '#' },
        { prop: 'name', label: '用户名', width: 140 },
        { prop: 'email', label: '邮箱', minWidth: 200 },
        {
          prop: 'roles',
          label: '角色',
          width: 120,
          useSlot: true
        },
        {
          prop: 'is_active',
          label: '状态',
          width: 90,
          useSlot: true
        },
        {
          prop: 'last_login',
          label: '最后登录',
          width: 170,
          formatter: (row: Api.SystemManage.UserListItem) => {
            if (!row.last_login) return '-'
            return new Date(row.last_login).toLocaleString('zh-CN')
          }
        },
        {
          prop: 'action',
          label: '操作',
          width: 150,
          fixed: 'right' as const,
          formatter: (row: Api.SystemManage.UserListItem) => {
            if (row.id === 0) {
              return h('span', { class: 'text-xs text-g-400' }, '超级管理员')
            }
            return h('div', { class: 'flex gap-1' }, [
              h(LfpButtonTable, { type: 'edit', onClick: () => openEdit(row) }),
              h(LfpButtonTable, { type: 'reset', onClick: () => openResetPwd(row) }),
              h(LfpButtonTable, { type: 'delete', onClick: () => handleDelete(row) })
            ])
          }
        }
      ]
    }
  })

  // ── 搜索 ──────────────────────────────────────
  const handleSearch = () => {
    refreshData()
  }

  const handleReset = () => {
    ;(searchParams as any).keyword = ''
    resetSearchParams()
  }

  // ── 编辑弹窗 ──────────────────────────────────
  const editVisible = ref(false)
  const editLoading = ref(false)
  const editUser = ref<Api.SystemManage.UserListItem | null>(null)
  const editForm = reactive({ is_active: true, is_admin: false })

  const openEdit = (row: Api.SystemManage.UserListItem) => {
    editUser.value = row
    editForm.is_active = row.is_active
    editForm.is_admin = row.is_admin
    editVisible.value = true
  }

  const handleEditSubmit = async () => {
    if (!editUser.value) return
    editLoading.value = true
    try {
      if (editForm.is_active !== editUser.value.is_active) {
        await fetchToggleUserActive(editUser.value.id, { is_active: editForm.is_active })
      }
      if (editForm.is_admin !== editUser.value.is_admin) {
        await fetchSetUserAdmin(editUser.value.id, { is_admin: editForm.is_admin })
      }
      ElMessage.success('保存成功')
      editVisible.value = false
      refreshData()
    } catch (e: any) {
      ElMessage.error(e?.message || '操作失败')
    } finally {
      editLoading.value = false
    }
  }

  // ── 重置密码 ──────────────────────────────────
  const resetPwdVisible = ref(false)
  const resetPwdLoading = ref(false)
  const resetPwdUser = ref<Api.SystemManage.UserListItem | null>(null)
  const resetPwdFormRef = ref<FormInstance>()
  const resetPwdForm = reactive({ new_password: '' })
  const resetPwdRules: FormRules = {
    new_password: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 8, message: '密码长度不少于8位', trigger: 'blur' }
    ]
  }

  const openResetPwd = (row: Api.SystemManage.UserListItem) => {
    resetPwdUser.value = row
    resetPwdForm.new_password = ''
    resetPwdVisible.value = true
  }

  const handleResetPassword = async () => {
    if (!resetPwdFormRef.value) return
    const valid = await resetPwdFormRef.value.validate().catch(() => false)
    if (!valid) return
    if (!resetPwdUser.value) return

    resetPwdLoading.value = true
    try {
      await fetchResetUserPassword(resetPwdUser.value.id, { new_password: resetPwdForm.new_password })
      ElMessage.success('密码已重置')
      resetPwdVisible.value = false
    } catch (e: any) {
      ElMessage.error(e?.message || '重置失败')
    } finally {
      resetPwdLoading.value = false
    }
  }

  // ── 删除 ──────────────────────────────────────
  const handleDelete = (row: Api.SystemManage.UserListItem) => {
    ElMessageBox.confirm(
      `确定要删除用户「${row.name}」吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    ).then(async () => {
      try {
        await fetchDeleteUser(row.id)
        ElMessage.success('删除成功')
        refreshData()
      } catch (e: any) {
        ElMessage.error(e?.message || '删除失败')
      }
    }).catch(() => {})
  }
</script>
