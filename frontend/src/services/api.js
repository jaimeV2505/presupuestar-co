import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 600000 })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401 && !window.location.pathname.startsWith('/p/')) {
    localStorage.removeItem('token')
    if (window.location.pathname !== '/login' && window.location.pathname !== '/registro') {
      window.location.href = '/login'
    }
  }
  let msg = err.message || 'Error de conexión'
  const detail = err.response?.data?.detail
  if (detail) {
    if (Array.isArray(detail)) {
      msg = detail.slice(0, 3).map(e => {
        const campo = (e.loc || []).slice(1).join('.')
        return campo ? `${campo}: ${e.msg}` : e.msg
      }).join(' | ')
    } else if (typeof detail === 'string') {
      msg = detail
    } else {
      msg = JSON.stringify(detail).slice(0, 200)
    }
  }
  return Promise.reject(new Error(msg))
})

export const authAPI = {
  registro: (data) => api.post('/auth/registro', data).then(r => r.data),
  login: (data) => api.post('/auth/login', data).then(r => r.data),
  yo: () => api.get('/auth/yo').then(r => r.data),
  actualizarPerfil: (data) => api.put('/auth/perfil', data).then(r => r.data),
}

export const proyectosAPI = {
  listar: () => api.get('/proyectos').then(r => r.data),
  crear: (data) => api.post('/proyectos', data).then(r => r.data),
  obtener: (id) => api.get(`/proyectos/${id}`).then(r => r.data),
  actualizar: (id, data) => api.put(`/proyectos/${id}`, data).then(r => r.data),
  eliminar: (id) => api.delete(`/proyectos/${id}`).then(r => r.data),
  duplicar: (id) => api.post(`/proyectos/${id}/duplicar`).then(r => r.data),
}

export const shareAPI = {
  compartir: (id) => api.post(`/share/proyectos/${id}/compartir`).then(r => r.data),
  eventos: (id) => api.get(`/share/proyectos/${id}/eventos`).then(r => r.data),
  verPublico: (token) => api.get(`/share/publico/${token}`).then(r => r.data),
  aceptar: (token, firma) => api.post(`/share/publico/${token}/aceptar`, firma).then(r => r.data),
  rechazar: (token) => api.post(`/share/publico/${token}/rechazar`).then(r => r.data),
  contrato: (token) => api.get(`/share/publico/${token}/contrato`).then(r => r.data),
  encuesta: (token, data) => api.post(`/share/publico/${token}/encuesta`, data).then(r => r.data),
  verEncuesta: (id) => api.get(`/share/proyectos/${id}/encuesta`).then(r => r.data),
}

export const avancesAPI = {
  listar: (id) => api.get(`/avances/proyectos/${id}/avances`).then(r => r.data),
  crear: (id, data) => api.post(`/avances/proyectos/${id}/avances`, data).then(r => r.data),
  eliminar: (id, avanceId) => api.delete(`/avances/proyectos/${id}/avances/${avanceId}`).then(r => r.data),
  publicos: (token) => api.get(`/share/publico/${token}/avances`).then(r => r.data),
}

export const preciosAPI = {
  buscar: (params) => api.get('/precios/', { params }).then(r => r.data),
  regiones: () => api.get('/precios/regiones').then(r => r.data),
  stats: () => api.get('/precios/stats').then(r => r.data),
}

export const exportarAPI = {
  excel: (payload) => api.post('/exportar/excel', payload, { responseType: 'blob' }),
  pdf: (payload) => api.post('/exportar/pdf', payload, { responseType: 'blob' }),
}

export default api
