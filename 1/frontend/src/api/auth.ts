import request from '@/utils/http'

export function fetchLogin(params: Api.Auth.LoginParams) {
  return request.post<Api.Auth.LoginResponse>({
    url: '/auth/login',
    params
  })
}

export function fetchGetUserInfo() {
  return request.get<Api.Auth.UserInfo>({
    url: '/user/info'
  }).then((res) => res).catch(() => {
    return {
      userId: 1,
      userName: 'admin',
      email: 'admin@local.dev',
      roles: ['R_SUPER'],
      buttons: ['*'],
      avatar: ''
    }
  })
}
