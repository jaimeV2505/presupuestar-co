import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Users, MessageCircle, ChevronDown } from 'lucide-react'
import { clientesAPI } from '../services/api'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

const ESTADOS = {
  borrador: 'bg-slate-100 text-slate-500', enviado: 'bg-blue-100 text-blue-600',
  visto: 'bg-violet-100 text-violet-600', aceptado: 'bg-emerald-100 text-emerald-700',
  rechazado: 'bg-red-100 text-red-600', entrega_solicitada: 'bg-violet-100 text-violet-700',
  terminado: 'bg-amber-100 text-amber-700',
}

export default function Clientes() {
  const nav = useNavigate()
  const [clientes, setClientes] = useState(null)
  const [abierto, setAbierto] = useState(null)

  useEffect(() => {
    clientesAPI.listar().then(setClientes).catch(e => toast.error(e.message))
  }, [])

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-navy-800 text-white">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={() => nav('/')} className="p-2 hover:bg-white/10 rounded-lg">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <h1 className="font-semibold flex items-center gap-2">
            <Users className="w-4 h-4" /> Mis clientes
          </h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">
        {clientes === null ? (
          <p className="text-center text-sm text-slate-400 py-10">Cargando...</p>
        ) : clientes.length === 0 ? (
          <div className="text-center py-14">
            <Users className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-500">Aún no tienes clientes</p>
            <p className="text-xs text-slate-400 mt-1">
              Se crean automáticamente al hacer presupuestos con nombre de cliente
            </p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {clientes.map(c => (
              <div key={c.id} className="bg-white rounded-xl border border-slate-100">
                <button onClick={() => setAbierto(abierto === c.id ? null : c.id)}
                        className="w-full flex items-center gap-3 p-4 text-left">
                  <div className="w-10 h-10 bg-navy-50 rounded-xl flex items-center justify-center shrink-0">
                    <span className="text-sm font-bold text-navy-600">
                      {c.nombre.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-700 truncate">
                      {c.nombre}
                      {c.calificacion && <span className="ml-2 text-[11px] text-amber-500">⭐ {c.calificacion}</span>}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      {c.n_proyectos} proyecto{c.n_proyectos !== 1 ? 's' : ''}
                      {c.n_terminados > 0 && ` · ${c.n_terminados} terminado${c.n_terminados !== 1 ? 's' : ''}`}
                      {c.telefono && ` · ${c.telefono}`}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-bold text-slate-700">{COP(c.total_contratado)}</p>
                    <p className="text-[10px] text-emerald-600">pagado {COP(c.pagado)}</p>
                  </div>
                  <ChevronDown className={`w-4 h-4 text-slate-300 shrink-0 transition ${abierto === c.id ? 'rotate-180' : ''}`} />
                </button>

                {abierto === c.id && (
                  <div className="border-t border-slate-50 px-4 py-3">
                    {c.telefono && (
                      <a href={`https://wa.me/${c.telefono.replace(/\D/g, '').replace(/^(?!57)/, '57')}`}
                         target="_blank" rel="noreferrer"
                         className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-600 border border-emerald-200 rounded-lg px-2.5 py-1.5 mb-3">
                        <MessageCircle className="w-3.5 h-3.5" /> Escribir por WhatsApp
                      </a>
                    )}
                    <div className="space-y-1.5">
                      {c.proyectos.map(p => (
                        <button key={p.id} onClick={() => nav(`/proyecto/${p.id}`)}
                                className="w-full flex items-center justify-between gap-2 hover:bg-slate-50 rounded-lg px-2 py-1.5 transition text-left">
                          <span className="text-xs text-slate-600 truncate">
                            <span className="text-slate-400">{p.numero}</span> · {p.nombre}
                          </span>
                          <span className={`shrink-0 text-[9px] font-medium px-2 py-0.5 rounded-full ${ESTADOS[p.estado] || ESTADOS.borrador}`}>
                            {p.estado.replace('_', ' ')}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
