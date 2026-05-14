import request from '@/utils/http'

/** 管理员 - 获取用户列表（分页+搜索） */
export function fetchGetUserList(params: Api.SystemManage.UserSearchParams) {
  return request.get<Api.SystemManage.UserList>({
    url: '/admin/users',
    params
  })
}

/** 管理员 - 切换用户启用/禁用 */
export function fetchToggleUserActive(userId: number, data: Api.SystemManage.ToggleActiveRequest) {
  return request.patch<Api.SystemManage.AdminOperationResponse>({
    url: `/admin/users/${userId}/active`,
    data
  })
}

/** 管理员 - 设置/取消管理员 */
export function fetchSetUserAdmin(userId: number, data: Api.SystemManage.SetAdminRequest) {
  return request.patch<Api.SystemManage.AdminOperationResponse>({
    url: `/admin/users/${userId}/admin`,
    data
  })
}

/** 管理员 - 重置用户密码 */
export function fetchResetUserPassword(userId: number, data: Api.SystemManage.ResetPasswordRequest) {
  return request.post<Api.SystemManage.AdminOperationResponse>({
    url: `/admin/users/${userId}/reset-password`,
    data
  })
}

/** 管理员 - 删除用户 */
export function fetchDeleteUser(userId: number) {
  return request.del<Api.SystemManage.AdminOperationResponse>({
    url: `/admin/users/${userId}`
  })
}
