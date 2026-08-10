import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Plus, FileText, Eye, CheckCircle2, Copy, Trash2, LogOut, Settings, Building2 } from 'lucide-react'
import { proyectosAPI } from '../services/api'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

const ESTADO_BADGE = {
  borrador:  { txt: 'Borrador', cls: 'bg-slate-100 text-slate-600' },
  enviado:   { txt: 'Enviado', cls: 'bg-blue-100 text-blue-700' },
  visto:     { txt: '👁 Visto', cls: 'bg-violet-100 text-violet-700' },
  aceptado:  { txt: '✓ Aceptado', cls: 'bg-emerald-100 text-emerald-700' },
  rechazado: { txt: '✕ Rechazado', cls: 'bg-red-100 text-red-600' },
  terminado: { txt: '🏁 Terminado', cls: 'bg-amber-100 text-amber-700' },
}

export default function Dashboard() {
  const nav = useNavigate()
  const [proyectos, setProyectos] = useState([])
  const [loading, setLoading] = useState(true)
  const [showNuevo, setShowNuevo] = useState(false)
  const [nuevo, setNuevo] = useState({ nombre: '', cliente_nombre: '', cliente_telefono: '', region: 'bogota' })
  const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')

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
            {usuario.plan === 'gratis' && (
              <span className="text-xs bg-white/10 px-3 py-1.5 rounded-full">Plan Gratis</span>
            )}
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
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-800">Mis presupuestos</h2>
          <button onClick={() => setShowNuevo(true)}
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
            <button onClick={() => setShowNuevo(true)}
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

      {/* Modal nuevo proyecto */}
      {showNuevo && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setShowNuevo(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800">Nuevo presupuesto</h3>
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
              <button onClick={crear} className="flex-1 py-2.5 rounded-xl bg-navy-600 text-white text-sm font-medium">
                Crear y editar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
