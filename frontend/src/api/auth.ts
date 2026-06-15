import request from './request'

export function login(email: string, password: string) {
  return request.post('/auth/login', { email, password })
}

export function register(username: string, email: string, password: string) {
  return request.post('/auth/register', { username, email, password })
}

export function refreshToken(refresh_token: string) {
  return request.post('/auth/refresh', { refresh_token })
}

export function getMe() {
  return request.get('/auth/me')
}

export function updateProfile(data: { username?: string; email?: string }) {
  return request.put('/auth/profile', data)
}

export function changePassword(data: { current_password: string; new_password: string }) {
  return request.post('/auth/change-password', data)
}
