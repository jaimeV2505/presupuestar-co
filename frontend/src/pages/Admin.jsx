import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
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

  const cargar = () => {
    setCargando(true)
    pagosAPI.adminSolicitudes()
      .then(setSolicitudes)
      .catch(e => { toast.error(e.message); if (e.message.includes('autorizado')) nav('/') })
      .finally(() => setCargando(false))
    soporteAPI.adminListar().then(setTickets).catch(() => {})
  }
  useEffect(() => { cargar() }, [])

  const aprobar = async (s) => {
    if (!confirm(`¿Activar Pro por 30 días para ${s.usuario.email}?`)) return
    try {
      const r = await pagosAPI.adminAprobar({ solicitud_id: s.id, dias: 30 })
      toast.success(`Pro activo para ${r.usuario} hasta ${r.vence}`)
      cargar()
    } catch (e) { toast.error(e.message) }
  }

  const rechazar = async (s) => {
    if (!confirm(`¿Rechazar la solicitud de ${s.usuario.email}?`)) return
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
            🛟 Tickets de soporte {tickets.filter(t => t.estado === 'abierto').length > 0 &&
              <span className="text-red-500">({tickets.filter(t => t.estado === 'abierto').length} abiertos)</span>}
          </h3>
          {tickets.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center bg-white rounded-xl border border-slate-100">Sin tickets</p>
          ) : (
            <div className="space-y-2">
              {tickets.slice(0, 30).map(t => (
                <div key={t.id} className={`bg-white rounded-xl border p-4 ${t.estado === 'abierto' ? 'border-red-200' : 'border-slate-100 opacity-60'}`}>
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

                  {t.respuesta && (
                    <div className="mt-2 bg-navy-50 border border-navy-100 rounded-lg p-2.5">
                      <p className="text-[10px] font-bold text-navy-600 mb-0.5">💬 Tu respuesta</p>
                      <p className="text-[11px] text-slate-600 whitespace-pre-wrap">{t.respuesta}</p>
                    </div>
                  )}

                  {t.estado === 'abierto' && (
                    <div className="mt-3 flex gap-2">
                      <input className="input flex-1 !py-2 text-xs"
                             placeholder="Escribe la respuesta al usuario..."
                             value={respuestas[t.id] || ''}
                             onChange={e => setRespuestas(r => ({ ...r, [t.id]: e.target.value }))} />
                      <button onClick={async () => {
                                const txt = (respuestas[t.id] || '').trim()
                                if (!txt) { toast.error('Escribe la respuesta'); return }
                                try {
                                  await soporteAPI.adminResponder({ ticket_id: t.id, respuesta: txt, resolver: true })
                                  setTickets(prev => prev.map(x => x.id === t.id ? { ...x, estado: 'resuelto', respuesta: txt } : x))
                                  toast.success('Respondido y resuelto — el usuario lo verá en su panel')
                                } catch (e2) { toast.error(e2.message) }
                              }}
                              className="shrink-0 text-xs font-bold bg-emerald-500 text-white px-3 py-2 rounded-lg">
                        Responder ✓
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
