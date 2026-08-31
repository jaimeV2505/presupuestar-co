import axios from 'axios'

// timeout 120s: si Vercel se cuelga, fallar-y-reintentar > esperar 10 min
const api = axios.create({ baseURL: '/api', timeout: 120000 })

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
  // NUNCA crear un Error nuevo aqui — eso descarta err.response, y el resto de
  // la app (ej. _enviar en Editor.jsx: `const esRed = !e.response`) depende de
  // esa propiedad para distinguir un error REAL del servidor (400/404/500, ya
  // respondio) de un problema de red genuino (nunca respondio). Perderla hacia
  // que CUALQUIER error de validacion se mostrara como "servidor lento" en vez
  // del mensaje real. Se enriquece el mensaje sobre el MISMO error original.
  err.message = msg
  return Promise.reject(err)
})

export const authAPI = {
  registro: (data) => api.post('/auth/registro', data).then(r => r.data),
  login: (data) => api.post('/auth/login', data).then(r => r.data),
  yo: () => api.get('/auth/yo').then(r => r.data),
  actualizarPerfil: (data) => api.put('/auth/perfil', data).then(r => r.data),
}

export const proyectosAPI = {
  analisis: (meses = 12, universo = 'todos') => api.get(`/proyectos/analisis?meses=${meses}&universo=${universo}`).then(r => r.data),
  balance: (id) => api.get(`/proyectos/${id}/balance`).then(r => r.data),
  listar: () => api.get('/proyectos').then(r => r.data),
  crear: (data) => api.post('/proyectos', data).then(r => r.data),
  obtener: (id) => api.get(`/proyectos/${id}`).then(r => r.data),
  actualizar: (id, data) => api.put(`/proyectos/${id}`, data).then(r => r.data),
  eliminar: (id) => api.delete(`/proyectos/${id}`).then(r => r.data),
  duplicar: (id, data) => api.post(`/proyectos/${id}/duplicar`, data || {}).then(r => r.data),
  terminar: (id) => api.post(`/proyectos/${id}/terminar`).then(r => r.data),
  metricas: () => api.get('/proyectos/metricas').then(r => r.data),
  plantillas: () => api.get('/proyectos/plantillas').then(r => r.data),
  desdePlantilla: (data) => api.post('/proyectos/desde-plantilla', data).then(r => r.data),
}

export const insumosAPI = {
  catalogo: (categoria) => api.get('/insumos/catalogo', { params: categoria ? { categoria } : {} }).then(r => r.data),
  buscar: (q) => api.get('/insumos/buscar', { params: { q } }).then(r => r.data),
  comparar: (q) => api.get('/insumos/comparar', { params: { q } }).then(r => r.data),
}

export const apusAPI = {
  listar: (params) => api.get('/apus', { params }).then(r => r.data),
  crear: (data) => api.post('/apus', data).then(r => r.data),
  duplicarDeBase: (codigo, region) => api.post(`/apus/duplicar-de-base?codigo=${encodeURIComponent(codigo)}&region=${region || 'bogota'}`).then(r => r.data),
  desgloseBase: (codigo, region) => api.get(`/apus/desglose-base/${encodeURIComponent(codigo)}`, { params: { region: region || 'bogota' } }).then(r => r.data),
  componer: (data) => api.post('/apus/componer', data).then(r => r.data),
  actualizar: (id, data) => api.put(`/apus/${id}`, data).then(r => r.data),
  guardarDesglose: (id, data) => api.put(`/apus/${id}/desglose`, data).then(r => r.data),
  recetario: () => api.post('/apus/recetario').then(r => r.data),
  eliminar: (id) => api.delete(`/apus/${id}`).then(r => r.data),
}

export const proveedoresAPI = {
  listar: () => api.get('/proveedores').then(r => r.data),
  crear: (data) => api.post('/proveedores', data).then(r => r.data),
  eliminar: (id) => api.delete(`/proveedores/${id}`).then(r => r.data),
  precios: (id) => api.get(`/proveedores/${id}/precios`).then(r => r.data),
  agregarPrecio: (id, data) => api.post(`/proveedores/${id}/precios`, data).then(r => r.data),
  eliminarPrecio: (precioId) => api.delete(`/proveedores/precios/${precioId}`).then(r => r.data),
  cargarMasivo: (id, formData) => api.post(`/proveedores/${id}/precios/masivo`, formData).then(r => r.data),
  resolverConflictos: (decisiones) => api.post('/proveedores/precios/resolver-conflictos', { decisiones }).then(r => r.data),
}

export const shareAPI = {
  disenos: (token) => api.get(`/share/publico/${token}/disenos`).then(r => r.data),
  comentarDiseno: (token, did, data) => api.post(`/share/publico/${token}/disenos/${did}/comentario`, data).then(r => r.data),
  interactuar: (token, avanceId, data) => api.post(`/share/publico/${token}/avances/${avanceId}/interaccion`, data).then(r => r.data),
  otrosiAprobar: (token, id, firma) => api.post(`/share/publico/${token}/otrosi/${id}/aprobar`, firma).then(r => r.data),
  otrosiRechazar: (token, id, motivo) => api.post(`/share/publico/${token}/otrosi/${id}/rechazar`, { motivo }).then(r => r.data),
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
  interacciones: (pid) => api.get(`/avances/proyectos/${pid}/interacciones`).then(r => r.data),
  responder: (avanceId, texto) => api.post(`/avances/${avanceId}/responder`, { texto }).then(r => r.data),
  responderComentario: (avanceId, texto) => api.post(`/avances/${avanceId}/responder`, { texto }).then(r => r.data),
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
  adminUsuarios: () => api.get('/pagos/admin/usuarios').then(r => r.data),
}

export const recuperarAPI = {
  olvide: (email) => api.post('/auth/olvide', { email }).then(r => r.data),
  restablecer: (data) => api.post('/auth/restablecer', data).then(r => r.data),
}

export const otrosiesAPI = {
  aprobarInterno: (id) => api.post(`/otrosies/${id}/aprobar-interno`).then(r => r.data),
  listar: (proyectoId) => api.get(`/otrosies/${proyectoId}`).then(r => r.data),
  crear: (data) => api.post('/otrosies', data).then(r => r.data),
  eliminar: (id) => api.delete(`/otrosies/${id}`).then(r => r.data),
}

export const cronogramaAPI = {
  obtener: (proyectoId) => api.get(`/cronograma/${proyectoId}`).then(r => r.data),
  guardar: (proyectoId, filas) => api.put(`/cronograma/${proyectoId}`, { filas }).then(r => r.data),
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
  anticipo: (pid) => post(`/cuentas/proyectos/${pid}/anticipo`),
  abonar: (cid, monto, nota) => api.post(`/cuentas/${cid}/abonos`, { monto, nota }).then(r => r.data),
  retegarantia: (pid) => api.post(`/cuentas/proyectos/${pid}/retegarantia`).then(r => r.data),
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
  varillas: () => api.get('/precios/varillas').then(r => r.data),
  dosificacion: (fc_mpa) => api.get('/precios/dosificacion-concreto', { params: { fc_mpa } }).then(r => r.data),
}

export const disenosAPI = {
  listar: (pid) => api.get(`/disenos/proyectos/${pid}/disenos`).then(r => r.data),
  crear: (pid, data) => api.post(`/disenos/proyectos/${pid}/disenos`, data).then(r => r.data),
  eliminar: (pid, did) => api.delete(`/disenos/proyectos/${pid}/disenos/${did}`).then(r => r.data),
  comentar: (pid, did, texto) => api.post(`/disenos/proyectos/${pid}/disenos/${did}/comentario`, { texto }).then(r => r.data),
}

export const exportarAPI = {
  excel: (payload) => api.post('/exportar/excel', payload, { responseType: 'blob' }),
  pdf: (payload) => api.post('/exportar/pdf', payload, { responseType: 'blob' }),
  apusPdf: (payload) => api.post('/exportar/apus-pdf', payload, { responseType: 'blob' }),
  explosion: (payload) => api.post('/exportar/explosion', payload).then(r => r.data),
  explosionExcel: (payload) => api.post('/exportar/explosion-excel', payload, { responseType: 'blob' }),
  cronogramaPdf: (payload) => api.post('/exportar/cronograma-pdf', payload, { responseType: 'blob' }),
}

export default api
