import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { confirmarDialogo } from '../components/Dialogo'
import { ArrowLeft, Crown, Check, X, RefreshCw } from 'lucide-react'
import { pagosAPI, soporteAPI } from '../services/api'

const ESTADO = {
  pendiente: 'bg-amber-100 text-amber-700',
  aprobada: 'bg-emerald-100 text-emerald-700',
  rechazada: 'bg-red-100 text-red-600',
}

export default function Admin() {
  const nav = useNavigate()
  const [solicitudes, setSolicitudes] = useState([])
  const [cargando, setCargando] = useState(true)
  const [manual, setManual] = useState({ email: '', dias: 30 })
  const [tickets, setTickets] = useState([])
  const [respuestas, setRespuestas] = useState({})  // {ticketId: texto}
  const [usuarios, setUsuarios] = useState([])

  const cargar = () => {
    setCargando(true)
    pagosAPI.adminSolicitudes()
      .then(setSolicitudes)
      .catch(e => { toast.error(e.message); if (e.message.includes('autorizado')) nav('/') })
      .finally(() => setCargando(false))
    soporteAPI.adminListar().then(setTickets).catch(() => {})
    pagosAPI.adminUsuarios().then(r => setUsuarios(r.usuarios || [])).catch(() => {})
  }
  useEffect(() => { cargar() }, [])

  const aprobar = async (s) => {
    if (!(await confirmarDialogo({ titulo: '⭐ ¿Activar Pro por 30 días?', mensaje: `Para ${s.usuario.email}`, confirmar: 'Activar Pro' }))) return
    try {
      const r = await pagosAPI.adminAprobar({ solicitud_id: s.id, dias: 30 })
      toast.success(`Pro activo para ${r.usuario} hasta ${r.vence}`)
      cargar()
    } catch (e) { toast.error(e.message) }
  }

  const rechazar = async (s) => {
    if (!(await confirmarDialogo({ titulo: '¿Rechazar la solicitud?', mensaje: `De ${s.usuario.email}`, peligro: true, confirmar: 'Rechazar' }))) return
    try {
      await pagosAPI.adminRechazar({ solicitud_id: s.id })
      toast.success('Rechazada')
      cargar()
    } catch (e) { toast.error(e.message) }
  }

  const activarManual = async () => {
    if (!manual.email.trim()) { toast.error('Escribe el email'); return }
    try {
      const r = await pagosAPI.adminPlanManual({ email: manual.email, plan: 'pro', dias: manual.dias })
      toast.success(`${r.usuario} → Pro hasta ${r.vence}`)
      setManual({ email: '', dias: 30 })
    } catch (e) { toast.error(e.message) }
  }

  const pendientes = solicitudes.filter(s => s.estado === 'pendiente')
  const resueltas = solicitudes.filter(s => s.estado !== 'pendiente')

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-navy-800 text-white">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => nav('/')} className="p-2 hover:bg-white/10 rounded-lg">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h1 className="font-semibold flex items-center gap-2"><Crown className="w-4 h-4 text-amber-400" /> Panel Admin — Pagos</h1>
          </div>
          <button onClick={cargar} className="p-2 hover:bg-white/10 rounded-lg">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {/* RESPALDO */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-5 flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p className="text-sm font-semibold text-slate-700">💾 Respaldo de la base de datos</p>
            <p className="text-[11px] text-slate-400">Descarga TODO (usuarios, proyectos, firmas, fotos) en un JSON. Hazlo cada semana y guárdalo en tu Drive.</p>
          </div>
          <button onClick={async () => {
                    try {
                      const res = await fetch('/api/respaldo/completo', {
                        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
                      })
                      if (!res.ok) throw new Error('No autorizado o error del servidor')
                      const blob = await res.blob()
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = `presupuestarco-backup-${new Date().toISOString().slice(0, 10)}.json`
                      a.click()
                      URL.revokeObjectURL(url)
                      toast.success('Backup descargado — guárdalo en tu Drive')
                    } catch (e) { toast.error(e.message) }
                  }}
                  className="shrink-0 text-xs font-bold bg-navy-600 text-white rounded-xl px-4 py-2.5">
            ⬇️ Descargar backup
          </button>
        </div>

        {/* USUARIOS REGISTRADOS — solo lectura, vision general */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-slate-700">
              👥 Usuarios registrados {usuarios.length > 0 && <span className="text-slate-400 font-normal">({usuarios.length})</span>}
            </p>
          </div>
          {usuarios.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">Sin usuarios aun</p>
          ) : (
            <div className="overflow-x-auto -mx-4 px-4">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-100">
                    <th className="py-2 pr-3 font-medium">Email</th>
                    <th className="py-2 pr-3 font-medium">Nombre</th>
                    <th className="py-2 pr-3 font-medium">Empresa</th>
                    <th className="py-2 pr-3 font-medium">Ciudad</th>
                    <th className="py-2 pr-3 font-medium">Plan</th>
                    <th className="py-2 pr-3 font-medium">Registrado</th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map(u => (
                    <tr key={u.id} className="border-b border-slate-50 last:border-0">
                      <td className="py-2 pr-3 text-slate-700 whitespace-nowrap">{u.email}</td>
                      <td className="py-2 pr-3 text-slate-600 whitespace-nowrap">{u.nombre}</td>
                      <td className="py-2 pr-3 text-slate-500 whitespace-nowrap">{u.empresa || '—'}</td>
                      <td className="py-2 pr-3 text-slate-500 whitespace-nowrap">{u.ciudad || '—'}</td>
                      <td className="py-2 pr-3 whitespace-nowrap">
                        <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${u.plan === 'pro' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-500'}`}>
                          {u.plan}
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-slate-400 whitespace-nowrap">{u.creado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Activacion manual directa */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Activar Pro directo (sin solicitud)</h3>
          <div className="flex gap-2">
            <input className="input flex-1" placeholder="email@delusuario.com"
                   value={manual.email} onChange={e => setManual(m => ({ ...m, email: e.target.value }))} />
            <input type="number" className="input w-20" min="1" max="400"
                   value={manual.dias} onChange={e => setManual(m => ({ ...m, dias: parseInt(e.target.value) || 30 }))} />
            <button onClick={activarManual}
                    className="bg-navy-600 text-white text-sm font-medium px-4 rounded-xl">
              Activar
            </button>
          </div>
        </div>

        {/* Pendientes */}
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            Solicitudes pendientes {pendientes.length > 0 && <span className="text-amber-600">({pendientes.length})</span>}
          </h3>
          {cargando ? (
            <p className="text-sm text-slate-400 py-4 text-center">Cargando...</p>
          ) : pendientes.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center bg-white rounded-xl border border-slate-100">Sin solicitudes pendientes</p>
          ) : (
            <div className="space-y-2">
              {pendientes.map(s => (
                <div key={s.id} className="bg-white rounded-xl border border-amber-200 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-700">{s.usuario.nombre} {s.usuario.empresa && `· ${s.usuario.empresa}`}</p>
                      <p className="text-xs text-slate-500">{s.usuario.email} · {s.usuario.telefono || 'sin tel'}</p>
                      <p className="text-[11px] text-slate-400 mt-1">
                        {s.fecha} · vía <strong>{s.metodo}</strong>
                        {s.referencia && <> · ref: <strong>{s.referencia}</strong></>}
                      </p>
                    </div>
                    <div className="flex gap-1.5 shrink-0">
                      <button onClick={() => aprobar(s)}
                              className="flex items-center gap-1 bg-emerald-500 text-white text-xs font-bold px-3 py-2 rounded-lg">
                        <Check className="w-3.5 h-3.5" /> Aprobar
                      </button>
                      <button onClick={() => rechazar(s)}
                              className="flex items-center gap-1 border border-slate-200 text-slate-500 text-xs px-3 py-2 rounded-lg">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tickets de soporte */}
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            🛟 Tickets de soporte {tickets.filter(t => t.estado === 'pendiente_soporte').length > 0 &&
              <span className="text-red-500">({tickets.filter(t => t.estado === 'pendiente_soporte').length} esperan tu respuesta)</span>}
          </h3>
          {tickets.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center bg-white rounded-xl border border-slate-100">Sin tickets</p>
          ) : (
            <div className="space-y-2">
              {tickets.slice(0, 30).map(t => (
                <div key={t.id} className={`bg-white rounded-xl border p-4 ${t.estado === 'pendiente_soporte' ? 'border-red-200' : t.estado === 'pendiente_cliente' ? 'border-blue-200' : 'border-slate-100 opacity-60'}`}>
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${t.estado === 'pendiente_soporte' ? 'bg-red-100 text-red-600' : t.estado === 'pendiente_cliente' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'}`}>
                    {t.estado === 'pendiente_soporte' ? '🔴 Te espera' : t.estado === 'pendiente_cliente' ? '🔵 Esperando al usuario' : '✓ Finalizado'}
                  </span>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-700">#{t.id} · {t.asunto}</p>
                      <p className="text-xs text-slate-500">{t.usuario.nombre} ({t.usuario.email}) · {t.usuario.telefono || 'sin tel'} · {t.fecha}</p>
                      {t.descripcion && <p className="text-xs text-slate-500 mt-1.5 whitespace-pre-wrap">{t.descripcion}</p>}
                      <p className="text-[10px] text-slate-300 mt-1">{t.contexto} · email: {t.email_enviado ? '✓ enviado' : '✗ solo BD'}</p>
                      {t.fotos?.length > 0 && (
                        <div className="flex gap-1.5 mt-2">
                          {t.fotos.map((f, i) => (
                            <a key={i} href={f} target="_blank" rel="noreferrer">
                              <img src={f} alt="" className="w-14 h-14 rounded-lg object-cover border border-slate-200" />
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {(t.mensajes || []).length > 0 && (
                    <div className="mt-2 space-y-1.5">
                      {t.mensajes.map((m, i) => (
                        <div key={i} className={`rounded-lg p-2.5 text-[11px] whitespace-pre-wrap border ${m.autor === 'soporte' ? 'bg-navy-50 border-navy-100' : 'bg-amber-50 border-amber-100'}`}>
                          <p className="text-[9px] font-bold mb-0.5 opacity-70">{m.autor === 'soporte' ? '🛟 Soporte (tú)' : `👤 ${t.usuario.nombre}`}{m.fecha && ` · ${m.fecha}`}</p>
                          {m.texto}
                        </div>
                      ))}
                    </div>
                  )}

                  {t.estado !== 'finalizado' && (
                    <div className="mt-3 flex gap-2">
                      <input className="input flex-1 !py-2 text-xs"
                             placeholder="Escribe la respuesta al usuario..."
                             value={respuestas[t.id] || ''}
                             onChange={e => setRespuestas(r => ({ ...r, [t.id]: e.target.value }))} />
                      <button onClick={async () => {
                                const txt = (respuestas[t.id] || '').trim()
                                if (!txt) { toast.error('Escribe la respuesta'); return }
                                try {
                                  await soporteAPI.adminResponder({ ticket_id: t.id, respuesta: txt })
                                  setTickets(prev => prev.map(x => x.id === t.id ? { ...x, estado: 'pendiente_cliente', mensajes: [...(x.mensajes || []), { autor: 'soporte', texto: txt, fecha: 'ahora' }] } : x))
                                  setRespuestas(r => ({ ...r, [t.id]: '' }))
                                  toast.success('Respuesta enviada — el usuario fue notificado 🔔')
                                } catch (e2) { toast.error(e2.message) }
                              }}
                              className="shrink-0 text-xs font-bold bg-navy-600 text-white px-3 py-2 rounded-lg">
                        Responder
                      </button>
                      <button onClick={async () => {
                                try {
                                  await soporteAPI.adminFinalizar(t.id)
                                  setTickets(prev => prev.map(x => x.id === t.id ? { ...x, estado: 'finalizado' } : x))
                                  toast.success('Ticket finalizado — el usuario fue notificado')
                                } catch (e2) { toast.error(e2.message) }
                              }}
                              className="shrink-0 text-xs font-bold bg-emerald-500 text-white px-3 py-2 rounded-lg"
                              title="Cierra el ticket (el usuario puede reabrirlo respondiendo)">
                        ✓ Finalizar
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Historial */}
        {resueltas.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Historial</h3>
            <div className="bg-white rounded-xl border border-slate-100 divide-y divide-slate-50">
              {resueltas.slice(0, 20).map(s => (
                <div key={s.id} className="px-4 py-2.5 flex items-center justify-between text-xs">
                  <span className="text-slate-600">{s.usuario.email} · {s.fecha}</span>
                  <span className={`px-2 py-0.5 rounded-full font-medium ${ESTADO[s.estado]}`}>{s.estado}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
