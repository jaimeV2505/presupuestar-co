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
    localStorage.removeItem('usuario')
    const path = window.location.pathname
    if (path === '/') {
      // En la raiz: mostrar la landing (sin sesion), no forzar login
      window.location.reload()
    } else if (path !== '/login' && path !== '/registro') {
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
  metricas: () => api.get('/proyectos/metricas').then(r => r.data),
  plantillas: () => api.get('/proyectos/plantillas').then(r => r.data),
  desdePlantilla: (data) => api.post('/proyectos/desde-plantilla', data).then(r => r.data),
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
  confirmarEntrega: (token, data) => api.post(`/share/publico/${token}/confirmar-entrega`, data).then(r => r.data),
  reportarPendientes: (token, detalle) => api.post(`/share/publico/${token}/reportar-pendientes`, { detalle }).then(r => r.data),
  perfilPublico: (slug) => api.get(`/share/c/${slug}`).then(r => r.data),
  miReputacion: () => api.get('/share/reputacion').then(r => r.data),
  publicarResena: (data) => api.post('/share/reputacion/publicar', data).then(r => r.data),
}

export const avancesAPI = {
  listar: (id) => api.get(`/avances/proyectos/${id}/avances`).then(r => r.data),
  crear: (id, data) => api.post(`/avances/proyectos/${id}/avances`, data).then(r => r.data),
  eliminar: (id, avanceId) => api.delete(`/avances/proyectos/${id}/avances/${avanceId}`).then(r => r.data),
  publicos: (token) => api.get(`/share/publico/${token}/avances`).then(r => r.data),
}

export const pagosAPI = {
  info: () => api.get('/pagos/info').then(r => r.data),
  solicitar: (data) => api.post('/pagos/solicitud', data).then(r => r.data),
  miSolicitud: () => api.get('/pagos/mi-solicitud').then(r => r.data),
  adminSolicitudes: () => api.get('/pagos/admin/solicitudes').then(r => r.data),
  adminAprobar: (data) => api.post('/pagos/admin/aprobar', data).then(r => r.data),
  adminRechazar: (data) => api.post('/pagos/admin/rechazar', data).then(r => r.data),
  adminPlanManual: (data) => api.post('/pagos/admin/plan-manual', data).then(r => r.data),
}

export const recuperarAPI = {
  olvide: (email) => api.post('/auth/olvide', { email }).then(r => r.data),
  restablecer: (data) => api.post('/auth/restablecer', data).then(r => r.data),
}

export const wompiAPI = {
  disponible: () => api.get('/wompi/disponible').then(r => r.data),
  link: () => api.post('/wompi/link').then(r => r.data),
  estado: (referencia) => api.get('/wompi/estado', { params: { referencia } }).then(r => r.data),
}

export const onboardingAPI = {
  estado: () => api.get('/onboarding').then(r => r.data),
  marcar: (clave) => api.post('/onboarding/marcar', { clave }).then(r => r.data),
  tipo: (tipo) => api.post('/onboarding/tipo', { tipo }).then(r => r.data),
}

export const clientesAPI = {
  listar: () => api.get('/clientes').then(r => r.data),
}

export const cuentasAPI = {
  listar: (pid) => api.get(`/cuentas/proyectos/${pid}/cuentas`).then(r => r.data),
  preview: (pid, avanceId) => api.get(`/cuentas/proyectos/${pid}/cuentas/preview`, { params: { avance_id: avanceId } }).then(r => r.data),
  crear: (pid, avanceId) => api.post(`/cuentas/proyectos/${pid}/cuentas`, { avance_id: avanceId }).then(r => r.data),
  pagada: (cid) => api.post(`/cuentas/${cid}/pagada`).then(r => r.data),
  eliminar: (cid) => api.delete(`/cuentas/${cid}`).then(r => r.data),
}

export const gastosAPI = {
  listar: (pid) => api.get(`/gastos/proyectos/${pid}/gastos`).then(r => r.data),
  crear: (pid, data) => api.post(`/gastos/proyectos/${pid}/gastos`, data).then(r => r.data),
  eliminar: (pid, gid) => api.delete(`/gastos/proyectos/${pid}/gastos/${gid}`).then(r => r.data),
}

export const notificacionesAPI = {
  listar: () => api.get('/notificaciones').then(r => r.data),
  leer: () => api.post('/notificaciones/leer').then(r => r.data),
}

export const soporteAPI = {
  crear: (data) => api.post('/soporte', data).then(r => r.data),
  adminListar: () => api.get('/soporte/admin').then(r => r.data),
  adminResponder: (data) => api.post('/soporte/admin/responder', data).then(r => r.data),
  adminFinalizar: (ticket_id) => api.post('/soporte/admin/finalizar', { ticket_id }).then(r => r.data),
  responder: (id, texto) => api.post(`/soporte/${id}/responder`, { texto }).then(r => r.data),
  misTickets: () => api.get('/soporte/mis-tickets').then(r => r.data),
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
