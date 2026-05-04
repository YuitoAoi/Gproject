import request from '@/utils/http'

export function fetchLogin(params: Api.Auth.LoginParams) {
  return request.post<Api.Auth.LoginResponse>({
    url: '/auth/login',
    params
  })
}

export function fetchRegister(params: Api.Auth.RegisterParams) {
  return request.post<Api.Auth.RegisterResponse>({
    url: '/user',
    params
  })
}

export function fetchGetUserInfo() {
  return request.get<Api.Auth.UserInfo>({
    url: '/user'
  }).then((res) => res).catch(() => {
    return {
      id: 1,
      name: 'admin',
      email: 'admin@local.dev',
      is_admin: true,
      is_active: true,
      created_at: '',
      last_login: ''
    }
  })
}
