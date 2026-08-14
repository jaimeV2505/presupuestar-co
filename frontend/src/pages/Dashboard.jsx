import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Plus, FileText, Eye, CheckCircle2, Copy, Trash2, LogOut, Settings, Building2, LifeBuoy, Camera, X, Bell, TrendingUp, Users } from 'lucide-react'
import { proyectosAPI, pagosAPI, soporteAPI, notificacionesAPI, clientesAPI, onboardingAPI } from '../services/api'
import { comprimirImagen } from '../utils/imagen'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

const ESTADO_BADGE = {
  borrador:  { txt: 'Borrador', cls: 'bg-slate-100 text-slate-600' },
  enviado:   { txt: 'Enviado', cls: 'bg-blue-100 text-blue-700' },
  visto:     { txt: '👁 Visto', cls: 'bg-violet-100 text-violet-700' },
  aceptado:  { txt: '✓ Aceptado', cls: 'bg-emerald-100 text-emerald-700' },
  rechazado: { txt: '✕ Rechazado', cls: 'bg-red-100 text-red-600' },
  terminado: { txt: '🏁 Terminado', cls: 'bg-amber-100 text-amber-700' },
  entrega_solicitada: { txt: '🤝 Por confirmar', cls: 'bg-violet-100 text-violet-700' },
}

export default function Dashboard() {
  const nav = useNavigate()
  const [proyectos, setProyectos] = useState([])
  const [loading, setLoading] = useState(true)
  const [showNuevo, setShowNuevo] = useState(false)
  const [nuevo, setNuevo] = useState({ nombre: '', cliente_nombre: '', cliente_telefono: '', region: 'bogota', sector: 'privado', entidad_nombre: '', contrato_numero: '', supervisor_nombre: '' })
  const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')
  const [infoPago, setInfoPago] = useState(null)
  const [showSoporte, setShowSoporte] = useState(false)
  const [respuestas, setRespuestas] = useState({})   // {ticketId: texto}
  const [ticket, setTicket] = useState({ asunto: '', descripcion: '', fotos: [] })
  const [enviandoTicket, setEnviandoTicket] = useState(false)
  const [ticketEnviado, setTicketEnviado] = useState(null)
  const [tabSoporte, setTabSoporte] = useState('nuevo')  // nuevo | mis
  const [misTickets, setMisTickets] = useState([])
  const [metricas, setMetricas] = useState(null)
  const [notifs, setNotifs] = useState({ no_leidas: 0, notificaciones: [] })
  const [showNotifs, setShowNotifs] = useState(false)
  const [plantillas, setPlantillas] = useState([])
  const [plantillaSel, setPlantillaSel] = useState(null)  // null = en blanco
  const [creandoTpl, setCreandoTpl] = useState(false)
  const [misClientes, setMisClientes] = useState([])
  const [onb, setOnb] = useState(null)  // estado del onboarding

  // Celebraciones de primera vez (usa las notificaciones cargadas)
  useEffect(() => {
    const lista = notifs.notificaciones || []
    if (lista.length === 0) return
    if (lista.some(x => x.tipo === 'firmado') && !localStorage.getItem('cel_firma')) {
      localStorage.setItem('cel_firma', '1')
      toast('🎉 ¡Tu primer contrato firmado! Ya puedes publicar avances de obra', { duration: 6000, icon: '✍️' })
    }
    if (lista.some(x => (x.tipo || '').includes('entrega')) && !localStorage.getItem('cel_entrega')) {
      localStorage.setItem('cel_entrega', '1')
      toast('🏁 ¡Primera entrega confirmada! La calificación de tu cliente alimenta tu reputación', { duration: 6000, icon: '🤝' })
    }
  }, [notifs])

  useEffect(() => {
    onboardingAPI.estado().then(setOnb).catch(() => {}); proyectosAPI.metricas().then(setMetricas).catch(() => {})
    const cargarNotifs = () => notificacionesAPI.listar().then(setNotifs).catch(() => {})
    cargarNotifs()
    const iv = setInterval(cargarNotifs, 30000)
    return () => clearInterval(iv)
  }, [])
  useEffect(() => { pagosAPI.info().then(setInfoPago).catch(() => {}) }, [])

  const cargar = async () => {
    try {
      setProyectos(await proyectosAPI.listar())
    } catch (e) { toast.error(e.message) }
    finally { setLoading(false) }
  }
  useEffect(() => { cargar() }, [])

  const crear = async () => {
    if (!nuevo.nombre.trim()) { toast.error('Ponle nombre al proyecto'); return }
    try {
      const p = await proyectosAPI.crear(nuevo)
      toast.success('Proyecto creado')
      nav(`/editor/${p.id}`)
    } catch (e) { toast.error(e.message) }
  }

  const duplicar = async (id, e) => {
    e.stopPropagation()
    try {
      const p = await proyectosAPI.duplicar(id)
      toast.success('Proyecto duplicado')
      cargar()
    } catch (e2) { toast.error(e2.message) }
  }

  const eliminar = async (id, e) => {
    e.stopPropagation()
    if (!confirm('¿Eliminar este presupuesto? No se puede deshacer.')) return
    try {
      await proyectosAPI.eliminar(id)
      toast.success('Eliminado')
      cargar()
    } catch (e2) { toast.error(e2.message) }
  }

  const salir = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('usuario')
    nav('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-navy-800 text-white">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/10 rounded-xl flex items-center justify-center">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold leading-tight">PresupuestarCO</h1>
              <p className="text-xs text-blue-200">{usuario.empresa || usuario.nombre}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {infoPago?.es_admin && (
              <button onClick={() => nav('/admin')} className="text-xs bg-amber-400/20 text-amber-300 px-3 py-1.5 rounded-full font-medium">
                Admin
              </button>
            )}
            {infoPago?.plan === 'pro' ? (
              <button onClick={() => nav('/pro')} className="text-xs bg-emerald-400/20 text-emerald-300 px-3 py-1.5 rounded-full font-bold">
                ⭐ Pro
              </button>
            ) : (
              <button onClick={() => nav('/pro')} className="text-xs bg-white/10 hover:bg-emerald-500/30 px-3 py-1.5 rounded-full transition">
                Plan Gratis → <span className="font-bold text-emerald-300">Pasar a Pro</span>
              </button>
            )}
            <button onClick={() => nav('/clientes')} className="p-2 hover:bg-white/10 rounded-lg" title="Mis clientes">
              <Users className="w-4 h-4" />
            </button>
            <div className="relative">
              <button onClick={() => {
                        setShowNotifs(v => !v)
                        if (!showNotifs && notifs.no_leidas > 0) {
                          notificacionesAPI.leer().then(() => setNotifs(n => ({ ...n, no_leidas: 0 }))).catch(() => {})
                        }
                      }} className="p-2 hover:bg-white/10 rounded-lg relative" title="Notificaciones">
                <Bell className="w-4 h-4" />
                {notifs.no_leidas > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[9px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-1">
                    {notifs.no_leidas > 9 ? '9+' : notifs.no_leidas}
                  </span>
                )}
              </button>
              {showNotifs && (
                <div className="absolute right-0 top-11 w-80 max-w-[85vw] bg-white rounded-2xl shadow-2xl border border-slate-100 z-50 overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-slate-100 flex justify-between items-center">
                    <p className="text-xs font-bold text-slate-700">Notificaciones</p>
                    <button onClick={() => setShowNotifs(false)}><X className="w-3.5 h-3.5 text-slate-400" /></button>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notifs.notificaciones.length === 0 ? (
                      <p className="text-center text-xs text-slate-400 py-8">Sin notificaciones aún</p>
                    ) : notifs.notificaciones.map(n => (
                      <button key={n.id}
                              onClick={() => {
                                setShowNotifs(false)
                                if (n.tipo === 'soporte') { setShowSoporte(true); setTabSoporte('mis'); return }
                                if (n.proyecto_id) nav(`/editor/${n.proyecto_id}`)
                              }}
                              className={`w-full text-left px-4 py-3 border-b border-slate-50 hover:bg-slate-50 transition ${!n.leida ? 'bg-blue-50/50' : ''}`}>
                        <p className="text-xs font-semibold text-slate-700">{n.icono} {n.titulo}</p>
                        {n.cuerpo && <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{n.cuerpo}</p>}
                        <p className="text-[9px] text-slate-300 mt-1">{n.fecha}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <button onClick={() => {
                      setShowSoporte(true); setTicketEnviado(null); setTabSoporte('nuevo')
                      soporteAPI.misTickets().then(setMisTickets).catch(() => {})
                    }} className="p-2 hover:bg-white/10 rounded-lg" title="Soporte">
              <LifeBuoy className="w-4 h-4" />
            </button>
            <button onClick={() => nav('/perfil')} className="p-2 hover:bg-white/10 rounded-lg" title="Perfil">
              <Settings className="w-4 h-4" />
            </button>
            <button onClick={salir} className="p-2 hover:bg-white/10 rounded-lg" title="Salir">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* METRICAS DEL NEGOCIO */}
        {metricas && metricas.n_presupuestos > 0 && (
          <div className="mb-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {[
                ['💰', 'Total cotizado', COP(metricas.total_cotizado), 'text-slate-800'],
                ['✅', 'Total ganado', COP(metricas.total_ganado), 'text-emerald-600'],
                ['💵', 'Utilidad proyectada', COP(metricas.utilidad_proyectada), 'text-emerald-600'],
                ['📈', 'Tasa de cierre', `${metricas.tasa_cierre}%`, 'text-navy-600'],
              ].map(([e, l, v, cls], i) => (
                <div key={i} className="bg-white rounded-xl border border-slate-100 p-3">
                  <p className="text-[10px] text-slate-400">{e} {l}</p>
                  <p className={`text-sm sm:text-base font-black mt-0.5 truncate ${cls}`}>{v}</p>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 px-1 text-[11px] text-slate-400">
              <span>🏗️ En ejecución: <strong className="text-slate-600">{metricas.en_ejecucion_n}</strong> ({COP(metricas.en_ejecucion_valor)})</span>
              <span>🏁 Terminadas: <strong className="text-slate-600">{metricas.n_terminados}</strong></span>
              {(metricas.cobrado > 0 || metricas.por_cobrar > 0) && (
                <span>💰 Cobrado: <strong className="text-emerald-600">{COP(metricas.cobrado)}</strong> · Por cobrar: <strong className="text-amber-600">{COP(metricas.por_cobrar)}</strong></span>
              )}
              {(metricas.cobrado > 0 || metricas.gastado > 0) && (
                <span>💼 Caja neta: <strong className={metricas.caja_neta >= 0 ? 'text-emerald-600' : 'text-red-500'}>{COP(metricas.caja_neta)}</strong></span>
              )}
              {metricas.calificacion && <span>⭐ Calificación: <strong className="text-amber-600">{metricas.calificacion}</strong> ({metricas.n_resenas} reseña{metricas.n_resenas !== 1 ? 's' : ''})</span>}
            </div>
          </div>
        )}

        {/* ONBOARDING: bienvenida */}
        {onb && !onb.tipo && !onb.cerrado && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-md text-center">
              <p className="text-3xl mb-2">👋</p>
              <h3 className="font-bold text-slate-800 mb-1">¡Bienvenido a PresupuestarCO!</h3>
              <p className="text-xs text-slate-400 mb-5">Una pregunta para acomodarte todo: ¿a qué te dedicas?</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'maestro', emoji: '👷', label: 'Maestro de obra' },
                  { id: 'remodelador', emoji: '🏠', label: 'Remodelador' },
                  { id: 'contratista', emoji: '🏗️', label: 'Contratista general' },
                ].map(t => (
                  <button key={t.id}
                          onClick={() => { onboardingAPI.tipo(t.id).catch(() => {}); setOnb(o => ({ ...o, tipo: t.id })) }}
                          className="border-2 border-slate-100 hover:border-navy-400 rounded-xl p-3 transition">
                    <span className="text-2xl">{t.emoji}</span>
                    <p className="text-[10px] font-semibold text-slate-600 mt-1 leading-tight">{t.label}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ONBOARDING: checklist de misiones */}
        {onb && onb.tipo && !onb.cerrado && (
          <div className="bg-white rounded-2xl border-2 border-navy-100 p-4 mb-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-bold text-slate-700">
                {onb.progreso === 100 ? '🎉 ¡Tu negocio está rodando!' : '🚀 Pon tu negocio a rodar'}
              </p>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-navy-600">{onb.progreso}%</span>
                <button onClick={() => { onboardingAPI.marcar('cerrado').catch(() => {}); setOnb(o => ({ ...o, cerrado: true })) }}
                        className="text-slate-300 hover:text-slate-500"><X className="w-4 h-4" /></button>
              </div>
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-3">
              <div className="h-full bg-navy-500 rounded-full transition-all" style={{ width: `${onb.progreso}%` }} />
            </div>
            <div className="space-y-1">
              {[
                { k: 'm1_presupuesto', label: 'Crea tu primer presupuesto', accion: () => { setShowNuevo(true); setPlantillaSel(null); proyectosAPI.plantillas().then(setPlantillas).catch(() => {}); clientesAPI.listar().then(setMisClientes).catch(() => {}) } },
                { k: 'm2_marca', label: 'Ponle tu marca (logo, cédula y firma)', accion: () => nav('/perfil') },
                { k: 'm3_whatsapp', label: 'Comparte un presupuesto por WhatsApp', accion: () => { const real = proyectos.find(p => !p.es_demo); real ? nav(`/editor/${real.id}`) : toast('Primero crea un presupuesto (misión 1)') } },
                { k: 'm4_vista_cliente', label: 'Mira lo que verá tu cliente', accion: () => { if (onb.demo) { window.open(`/p/${onb.demo.share_token}`, '_blank'); onboardingAPI.marcar('vista_cliente').catch(() => {}); setOnb(o => ({ ...o, misiones: { ...o.misiones, m4_vista_cliente: true }, progreso: Math.min(100, o.progreso + 20) })) } } },
                { k: 'm5_explora', label: 'Explora avances y cobros en el ejemplo', accion: () => { if (onb.demo) { onboardingAPI.marcar('explora').catch(() => {}); nav(`/editor/${onb.demo.id}`) } } },
              ].map(m => (
                <button key={m.k} onClick={m.accion} disabled={onb.misiones[m.k]}
                        className={`w-full flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-left transition ${onb.misiones[m.k] ? 'opacity-50' : 'hover:bg-slate-50'}`}>
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] shrink-0 ${onb.misiones[m.k] ? 'bg-emerald-500 text-white' : 'border-2 border-slate-200'}`}>
                    {onb.misiones[m.k] && '✓'}
                  </span>
                  <span className={`text-xs ${onb.misiones[m.k] ? 'text-slate-400 line-through' : 'text-slate-600 font-medium'}`}>{m.label}</span>
                  {!onb.misiones[m.k] && <span className="ml-auto text-[10px] text-navy-500">→</span>}
                </button>
              ))}
            </div>
            {onb.progreso === 100 && (
              <button onClick={() => { onboardingAPI.marcar('cerrado').catch(() => {}); setOnb(o => ({ ...o, cerrado: true })); toast.success('🎉 ¡Listo para cotizar como los grandes!') }}
                      className="w-full mt-3 py-2 rounded-xl bg-navy-600 text-white text-xs font-bold">
                🎉 ¡Completado! Cerrar la guía
              </button>
            )}
          </div>
        )}

        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-800">Mis presupuestos</h2>
          <button onClick={() => { setShowNuevo(true); setPlantillaSel(null); if (plantillas.length === 0) proyectosAPI.plantillas().then(setPlantillas).catch(() => {}); clientesAPI.listar().then(setMisClientes).catch(() => {}) }}
                  className="flex items-center gap-2 bg-navy-600 hover:bg-navy-700 text-white text-sm font-medium px-4 py-2.5 rounded-xl transition">
            <Plus className="w-4 h-4" /> Nuevo presupuesto
          </button>
        </div>

        {loading ? (
          <div className="text-center py-16 text-slate-400">Cargando...</div>
        ) : proyectos.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl border border-slate-200">
            <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-600 font-medium">Crea tu primer presupuesto</p>
            <p className="text-sm text-slate-400 mt-1 mb-4">Busca actividades, ajusta cantidades y comparte por WhatsApp</p>
            <button onClick={() => { setShowNuevo(true); setPlantillaSel(null); if (plantillas.length === 0) proyectosAPI.plantillas().then(setPlantillas).catch(() => {}); clientesAPI.listar().then(setMisClientes).catch(() => {}) }}
                    className="bg-navy-600 text-white text-sm font-medium px-5 py-2.5 rounded-xl">
              Empezar
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {proyectos.map(p => {
              const badge = ESTADO_BADGE[p.estado] || ESTADO_BADGE.borrador
              return (
                <div key={p.id} onClick={() => nav(`/editor/${p.id}`)}
                     className="bg-white rounded-xl border border-slate-200 p-4 hover:border-navy-300 hover:shadow-md transition cursor-pointer">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] font-bold text-navy-500 bg-navy-50 px-1.5 py-0.5 rounded">{p.es_demo ? '🎓 EJEMPLO' : p.numero}</span>
                        <h3 className="font-semibold text-slate-800">{p.nombre}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.cls}`}>{badge.txt}</span>
                      </div>
                      <p className="text-sm text-slate-400 mt-0.5">
                        {p.cliente_nombre && `${p.cliente_nombre} · `}
                        {p.num_items} ítem{p.num_items !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="font-bold text-slate-800">{COP(p.totales?.total)}</p>
                      {p.total_adicionales > 0 && (
                        <p className="text-[10px] font-bold text-amber-600">➕ {COP(p.total_adicionales)} en adicionales</p>
                      )}
                      <div className="flex items-center gap-1 mt-1.5 justify-end">
                        <button onClick={(e) => duplicar(p.id, e)} className="p-1.5 hover:bg-slate-100 rounded-lg" title="Duplicar">
                          <Copy className="w-3.5 h-3.5 text-slate-400" />
                        </button>
                        <button onClick={(e) => eliminar(p.id, e)} className="p-1.5 hover:bg-red-50 rounded-lg" title="Eliminar">
                          <Trash2 className="w-3.5 h-3.5 text-slate-400 hover:text-red-500" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>

      {/* Modal SOPORTE */}
      {showSoporte && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setShowSoporte(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            {ticketEnviado ? (
              <div className="text-center py-4">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-emerald-100 rounded-2xl mb-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                </div>
                <h3 className="font-semibold text-slate-800">Reporte #{ticketEnviado} recibido</h3>
                <p className="text-sm text-slate-500 mt-1.5">
                  Te respondemos por WhatsApp o email lo antes posible. ¡Gracias por ayudarnos a mejorar!
                </p>
                <button onClick={() => setShowSoporte(false)}
                        className="mt-5 w-full py-2.5 rounded-xl bg-navy-600 text-white text-sm font-medium">
                  Listo
                </button>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                    <LifeBuoy className="w-4 h-4 text-navy-500" /> Soporte
                  </h3>
                  <button onClick={() => setShowSoporte(false)} className="p-1 hover:bg-slate-100 rounded-lg">
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                </div>

                {/* Pestañas */}
                <div className="flex gap-1.5 mb-4 bg-slate-100 rounded-xl p-1">
                  <button onClick={() => setTabSoporte('nuevo')}
                          className={`flex-1 text-xs font-medium py-2 rounded-lg transition ${tabSoporte === 'nuevo' ? 'bg-white text-navy-600 shadow-sm' : 'text-slate-500'}`}>
                    Nuevo reporte
                  </button>
                  <button onClick={() => { setTabSoporte('mis'); soporteAPI.misTickets().then(setMisTickets).catch(() => {}) }}
                          className={`flex-1 text-xs font-medium py-2 rounded-lg transition ${tabSoporte === 'mis' ? 'bg-white text-navy-600 shadow-sm' : 'text-slate-500'}`}>
                    Mis reportes {misTickets.length > 0 && `(${misTickets.length})`}
                    {misTickets.some(t => t.estado === 'pendiente_cliente') && ' 💬'}
                  </button>
                </div>

                {tabSoporte === 'mis' ? (
                  <div className="space-y-2 max-h-[55vh] overflow-y-auto">
                    {misTickets.length === 0 ? (
                      <p className="text-center text-xs text-slate-400 py-8">Aún no has creado reportes</p>
                    ) : misTickets.map(t => {
                      const chip = t.estado === 'finalizado'
                        ? ['bg-slate-100 text-slate-500', '✓ Finalizado']
                        : t.estado === 'pendiente_cliente'
                          ? ['bg-blue-100 text-blue-700', '💬 Te respondieron']
                          : ['bg-amber-100 text-amber-700', '⏳ Esperando a soporte']
                      return (
                      <div key={t.id} className="border border-slate-200 rounded-xl p-3 bg-white">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-700">#{t.id} · {t.asunto}</p>
                            <p className="text-[10px] text-slate-400">{t.fecha}{t.num_fotos > 0 && ` · ${t.num_fotos} 📷`}</p>
                          </div>
                          <span className={`shrink-0 text-[10px] font-bold px-2 py-1 rounded-full ${chip[0]}`}>{chip[1]}</span>
                        </div>
                        {t.descripcion && <p className="text-[11px] text-slate-500 mt-1.5">{t.descripcion}</p>}

                        {(t.mensajes || []).length > 0 && (
                          <div className="mt-2 space-y-1.5">
                            {t.mensajes.map((m, i) => (
                              <div key={i} className={`rounded-lg p-2.5 text-[11px] whitespace-pre-wrap ${m.autor === 'soporte' ? 'bg-navy-50 border border-navy-100 text-slate-700' : 'bg-slate-50 border border-slate-100 text-slate-600'}`}>
                                <p className="text-[9px] font-bold mb-0.5 opacity-70">{m.autor === 'soporte' ? '🛟 Soporte' : '👤 Tú'}{m.fecha && ` · ${m.fecha}`}</p>
                                {m.texto}
                              </div>
                            ))}
                          </div>
                        )}

                        <div className="flex gap-2 mt-2">
                          <input className="input !py-2 text-xs flex-1"
                                 placeholder={t.estado === 'finalizado' ? 'Responder (reabre el ticket)...' : 'Responder...'}
                                 value={respuestas[t.id] || ''}
                                 onChange={e => setRespuestas(r => ({ ...r, [t.id]: e.target.value }))} />
                          <button onClick={async () => {
                                    const texto = (respuestas[t.id] || '').trim()
                                    if (!texto) return
                                    try {
                                      await soporteAPI.responder(t.id, texto)
                                      setRespuestas(r => ({ ...r, [t.id]: '' }))
                                      soporteAPI.misTickets().then(setMisTickets).catch(() => {})
                                      toast.success('Enviado a soporte')
                                    } catch (e) { toast.error(e.message) }
                                  }}
                                  className="text-xs font-bold bg-navy-600 text-white rounded-lg px-3">
                            Enviar
                          </button>
                        </div>
                      </div>
                    )})}
                  </div>
                ) : (
                <div className="space-y-3">
                  <input className="input" placeholder="¿Qué pasó? (ej: El PDF no descarga) *"
                         value={ticket.asunto} maxLength={200}
                         onChange={e => setTicket(t => ({ ...t, asunto: e.target.value }))} autoFocus />
                  <textarea className="input min-h-[100px] text-sm"
                            placeholder="Detalles: qué estabas haciendo, qué esperabas que pasara, qué pasó en cambio..."
                            value={ticket.descripcion} maxLength={4000}
                            onChange={e => setTicket(t => ({ ...t, descripcion: e.target.value }))} />
                  <div className="flex items-center gap-2 flex-wrap">
                    <label className="flex items-center gap-2 text-xs text-navy-600 font-medium border border-navy-200 rounded-xl px-3 py-2 cursor-pointer hover:bg-navy-50">
                      <Camera className="w-4 h-4" /> Evidencia ({ticket.fotos.length}/2)
                      <input type="file" accept="image/*" multiple className="hidden"
                             onChange={e => {
                               const files = Array.from(e.target.files || []).slice(0, 2 - ticket.fotos.length)
                               files.forEach(file => {
                                 if (file.size > 450 * 1024) { toast.error(`${file.name}: máximo 450KB`); return }
                                 comprimirImagen(file).then(f => setTicket(t => ({ ...t, fotos: [...t.fotos, f].slice(0, 2) }))).catch(() => toast.error('Imagen no valida'))
                               })
                               e.target.value = ''
                             }} />
                    </label>
                    {ticket.fotos.map((f, i) => (
                      <div key={i} className="relative">
                        <img src={f} alt="" className="w-10 h-10 rounded-lg object-cover border border-slate-200" />
                        <button onClick={() => setTicket(t => ({ ...t, fotos: t.fotos.filter((_, j) => j !== i) }))}
                                className="absolute -top-1.5 -right-1.5 bg-red-500 text-white rounded-full w-4 h-4 text-[9px] leading-none">×</button>
                      </div>
                    ))}
                  </div>
                  <button disabled={enviandoTicket}
                          onClick={async () => {
                            if (!ticket.asunto.trim()) { toast.error('Cuéntanos qué pasó'); return }
                            setEnviandoTicket(true)
                            try {
                              const res = await soporteAPI.crear({
                                ...ticket,
                                contexto: `pagina: ${window.location.pathname} · plan: ${infoPago?.plan || '?'} · ${navigator.userAgent.slice(0, 80)}`,
                              })
                              setTicketEnviado(res.ticket)
                              setTicket({ asunto: '', descripcion: '', fotos: [] })
                              soporteAPI.misTickets().then(setMisTickets).catch(() => {})
                            } catch (e) { toast.error(e.message) }
                            finally { setEnviandoTicket(false) }
                          }}
                          className="w-full py-3 rounded-xl bg-navy-600 hover:bg-navy-700 text-white text-sm font-bold transition disabled:opacity-50">
                    {enviandoTicket ? 'Enviando...' : 'Enviar reporte'}
                  </button>
                </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Modal nuevo proyecto */}
      {showNuevo && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setShowNuevo(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800">Nuevo presupuesto</h3>

            {/* Sector: obra privada u obra publica */}
            <div className="grid grid-cols-2 gap-1.5">
              {[['privado', '🏠 Obra privada', 'Cliente final con enlace y firma'],
                ['publico', '🏛️ Obra pública', 'Contrato estatal — control interno']].map(([v, t, s]) => (
                <button key={v} onClick={() => { setNuevo(n => ({ ...n, sector: v, ...(v === 'publico' ? { cliente_nombre: '', cliente_telefono: '' } : {}) })); if (v === 'publico') setPlantillaSel(null) }}
                        className={`rounded-xl border-2 p-2.5 text-left transition ${nuevo.sector === v ? 'border-navy-400 bg-navy-50' : 'border-slate-100'}`}>
                  <p className="text-xs font-bold text-slate-700">{t}</p>
                  <p className="text-[9px] text-slate-400 leading-tight mt-0.5">{s}</p>
                </button>
              ))}
            </div>

            {nuevo.sector === 'publico' && (
              <div className="space-y-2">
                <input className="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5"
                       placeholder="Entidad contratante (ej: Alcaldía de...)"
                       value={nuevo.entidad_nombre} onChange={e => setNuevo(n => ({ ...n, entidad_nombre: e.target.value }))} />
                <div className="flex gap-2">
                  <input className="flex-1 text-sm border border-slate-200 rounded-xl px-3 py-2.5"
                         placeholder="No. de contrato" value={nuevo.contrato_numero}
                         onChange={e => setNuevo(n => ({ ...n, contrato_numero: e.target.value }))} />
                  <input className="flex-1 text-sm border border-slate-200 rounded-xl px-3 py-2.5"
                         placeholder="Supervisor/interventor" value={nuevo.supervisor_nombre}
                         onChange={e => setNuevo(n => ({ ...n, supervisor_nombre: e.target.value }))} />
                </div>
              </div>
            )}

            {/* Plantillas */}
            {nuevo.sector === 'privado' && plantillas.length > 0 && (
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold mb-1.5">Empieza con una plantilla</p>
                <div className="grid grid-cols-3 gap-1.5 max-h-40 overflow-y-auto">
                  <button onClick={() => setPlantillaSel(null)}
                          className={`rounded-xl border-2 p-2 text-center transition ${plantillaSel === null ? 'border-navy-400 bg-navy-50' : 'border-slate-100'}`}>
                    <span className="text-lg">📄</span>
                    <p className="text-[10px] font-semibold text-slate-600 leading-tight mt-0.5">En blanco</p>
                  </button>
                  {[...plantillas].sort((a, b) => {
                    const orden = onb?.tipo === 'remodelador' ? ['bano', 'cocina', 'pintura', 'placa', 'cubierta', 'casa60']
                                : onb?.tipo === 'contratista' ? ['casa60', 'placa', 'cubierta', 'bano', 'cocina', 'pintura']
                                : ['bano', 'pintura', 'cocina', 'placa', 'cubierta', 'casa60']
                    return orden.indexOf(a.id) - orden.indexOf(b.id)
                  }).map(t => (
                    <button key={t.id} onClick={() => setPlantillaSel(t.id)}
                            title={t.descripcion}
                            className={`rounded-xl border-2 p-2 text-center transition ${plantillaSel === t.id ? 'border-emerald-400 bg-emerald-50' : 'border-slate-100'}`}>
                      <span className="text-lg">{t.emoji}</span>
                      <p className="text-[10px] font-semibold text-slate-600 leading-tight mt-0.5">{t.nombre}</p>
                      <p className="text-[8px] text-slate-400">{t.n_items} actividades</p>
                    </button>
                  ))}
                </div>
                {plantillaSel && (
                  <p className="text-[10px] text-emerald-600 mt-1.5 bg-emerald-50 rounded-lg p-2">
                    ✓ {plantillas.find(t => t.id === plantillaSel)?.descripcion} — luego ajustas cantidades y precios
                  </p>
                )}
              </div>
            )}

            <input className="input" placeholder="Nombre del proyecto * (ej: Remodelación cocina Casa López)"
                   value={nuevo.nombre} onChange={e => setNuevo(n => ({ ...n, nombre: e.target.value }))} autoFocus />
            {nuevo.sector === 'privado' && (<>
            <input className="input" placeholder="Nombre del cliente" list="lista-clientes"
                   value={nuevo.cliente_nombre}
                   onChange={e => {
                     const v = e.target.value
                     const match = misClientes.find(c => c.nombre === v)
                     setNuevo(n => ({ ...n, cliente_nombre: v,
                                      cliente_telefono: match?.telefono || n.cliente_telefono }))
                   }} />
            <datalist id="lista-clientes">
              {misClientes.map(c => <option key={c.id} value={c.nombre} />)}
            </datalist>
            <input className="input" placeholder="WhatsApp del cliente (ej: 300 123 4567)"
                   value={nuevo.cliente_telefono} onChange={e => setNuevo(n => ({ ...n, cliente_telefono: e.target.value }))} />
            </>)}
            <select className="input" value={nuevo.region} onChange={e => setNuevo(n => ({ ...n, region: e.target.value }))}>
              <option value="bogota">Bogotá D.C.</option>
              <option value="medellin">Medellín</option>
              <option value="cali">Cali</option>
              <option value="barranquilla">Barranquilla</option>
              <option value="bucaramanga">Bucaramanga</option>
              <option value="cartagena">Cartagena</option>
              <option value="pereira">Pereira</option>
              <option value="manizales">Manizales</option>
              <option value="ibague">Ibagué</option>
              <option value="cucuta">Cúcuta</option>
              <option value="villavicencio">Villavicencio</option>
              <option value="monteria">Montería</option>
              <option value="pasto">Pasto</option>
            </select>
            <div className="flex gap-2 pt-1">
              <button onClick={() => setShowNuevo(false)} className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium">
                Cancelar
              </button>
              <button disabled={creandoTpl}
                      onClick={async () => {
                        if (!plantillaSel) { crear(); return }
                        setCreandoTpl(true)
                        try {
                          const p = await proyectosAPI.desdePlantilla({ plantilla_id: plantillaSel, nombre: nuevo.nombre })
                          // Guardar cliente/region si los llenaron
                          const extra = {}
                          if (nuevo.cliente_nombre) extra.cliente_nombre = nuevo.cliente_nombre
                          if (nuevo.cliente_telefono) extra.cliente_telefono = nuevo.cliente_telefono
                          if (nuevo.region) extra.region = nuevo.region
                          if (Object.keys(extra).length) await proyectosAPI.actualizar(p.id, extra).catch(() => {})
                          toast.success(`Plantilla cargada con sus actividades — ajusta cantidades`)
                          nav(`/editor/${p.id}`)
                        } catch (e) { toast.error(e.message) }
                        finally { setCreandoTpl(false) }
                      }}
                      className="flex-1 py-2.5 rounded-xl bg-navy-600 text-white text-sm font-medium disabled:opacity-50">
                {creandoTpl ? 'Armando...' : plantillaSel ? '⚡ Crear con plantilla' : 'Crear y editar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
