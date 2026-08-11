import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Plus, FileText, Eye, CheckCircle2, Copy, Trash2, LogOut, Settings, Building2, LifeBuoy, Camera, X, Bell, TrendingUp } from 'lucide-react'
import { proyectosAPI, pagosAPI, soporteAPI, notificacionesAPI } from '../services/api'

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
  const [nuevo, setNuevo] = useState({ nombre: '', cliente_nombre: '', cliente_telefono: '', region: 'bogota' })
  const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')
  const [infoPago, setInfoPago] = useState(null)
  const [showSoporte, setShowSoporte] = useState(false)
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

  useEffect(() => {
    proyectosAPI.metricas().then(setMetricas).catch(() => {})
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
                              onClick={() => { if (n.proyecto_id) nav(`/proyecto/${n.proyecto_id}`) }}
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
              {metricas.calificacion && <span>⭐ Calificación: <strong className="text-amber-600">{metricas.calificacion}</strong> ({metricas.n_resenas} reseña{metricas.n_resenas !== 1 ? 's' : ''})</span>}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-800">Mis presupuestos</h2>
          <button onClick={() => setShowNuevo(true); setPlantillaSel(null); if (plantillas.length === 0) proyectosAPI.plantillas().then(setPlantillas).catch(() => {})}
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
            <button onClick={() => setShowNuevo(true); setPlantillaSel(null); if (plantillas.length === 0) proyectosAPI.plantillas().then(setPlantillas).catch(() => {})}
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
                        <span className="text-[10px] font-bold text-navy-500 bg-navy-50 px-1.5 py-0.5 rounded">{p.numero}</span>
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
                    {misTickets.some(t => t.estado === 'resuelto' && t.respuesta) && ' 💬'}
                  </button>
                </div>

                {tabSoporte === 'mis' ? (
                  <div className="space-y-2 max-h-[55vh] overflow-y-auto">
                    {misTickets.length === 0 ? (
                      <p className="text-center text-xs text-slate-400 py-8">Aún no has creado reportes</p>
                    ) : misTickets.map(t => (
                      <div key={t.id} className={`border rounded-xl p-3 ${t.estado === 'abierto' ? 'border-amber-200 bg-amber-50/40' : 'border-emerald-200 bg-emerald-50/30'}`}>
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-700">#{t.id} · {t.asunto}</p>
                            <p className="text-[10px] text-slate-400">{t.fecha}{t.num_fotos > 0 && ` · ${t.num_fotos} 📷`}</p>
                          </div>
                          <span className={`shrink-0 text-[10px] font-bold px-2 py-1 rounded-full ${t.estado === 'abierto' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                            {t.estado === 'abierto' ? '⏳ En revisión' : '✓ Resuelto'}
                          </span>
                        </div>
                        {t.descripcion && <p className="text-[11px] text-slate-500 mt-1.5 line-clamp-2">{t.descripcion}</p>}
                        {t.respuesta && (
                          <div className="mt-2 bg-white border border-slate-100 rounded-lg p-2.5">
                            <p className="text-[10px] font-bold text-navy-500 mb-0.5">💬 Respuesta del equipo{t.fecha_respuesta && ` · ${t.fecha_respuesta}`}</p>
                            <p className="text-[11px] text-slate-600 whitespace-pre-wrap">{t.respuesta}</p>
                          </div>
                        )}
                      </div>
                    ))}
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
                                 const r = new FileReader()
                                 r.onload = () => setTicket(t => ({ ...t, fotos: [...t.fotos, r.result].slice(0, 2) }))
                                 r.readAsDataURL(file)
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

            {/* Plantillas */}
            {plantillas.length > 0 && (
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold mb-1.5">Empieza con una plantilla</p>
                <div className="grid grid-cols-3 gap-1.5 max-h-40 overflow-y-auto">
                  <button onClick={() => setPlantillaSel(null)}
                          className={`rounded-xl border-2 p-2 text-center transition ${plantillaSel === null ? 'border-navy-400 bg-navy-50' : 'border-slate-100'}`}>
                    <span className="text-lg">📄</span>
                    <p className="text-[10px] font-semibold text-slate-600 leading-tight mt-0.5">En blanco</p>
                  </button>
                  {plantillas.map(t => (
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
            <input className="input" placeholder="Nombre del cliente"
                   value={nuevo.cliente_nombre} onChange={e => setNuevo(n => ({ ...n, cliente_nombre: e.target.value }))} />
            <input className="input" placeholder="WhatsApp del cliente (ej: 300 123 4567)"
                   value={nuevo.cliente_telefono} onChange={e => setNuevo(n => ({ ...n, cliente_telefono: e.target.value }))} />
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
                          nav(`/proyecto/${p.id}`)
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
