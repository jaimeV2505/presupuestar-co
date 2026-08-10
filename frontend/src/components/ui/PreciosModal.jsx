import React, { useState, useEffect, useMemo } from 'react'
import { X, Search, Loader2, Database, Filter, ChevronDown } from 'lucide-react'
import { preciosAPI } from '../../services/api'
import { COP } from '../../utils/format'

const CAT_ICONS = {
  'PRELIMINARES':'🔧','MOVIMIENTO DE TIERRAS':'⛏',
  'CIMENTACIONES':'⬇️','ESTRUCTURAS EN CONCRETO':'🏛',
  'ESTRUCTURA METÁLICA':'⚙️','CUBIERTAS':'🏠',
  'MAMPOSTERÍA':'🧱','PAÑETES (REVOQUES)':'🖌',
  'INSTALACIONES SANITARIAS':'🚿','INSTALACIONES HIDRÁULICAS':'💧',
  'INSTALACIONES ELÉCTRICAS':'⚡','PISOS':'📐',
  'ACABADOS':'✨','CARPINTERÍA METÁLICA':'🚪',
}

export default function PreciosModal({region, onClose}) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('')
  const [cats, setCats] = useState([])
  const [meta, setMeta] = useState({})
  const [total, setTotal] = useState(0)

  const load = async () => {
    setLoading(true)
    try {
      const res = await preciosAPI.getAll(region, cat||undefined, q||undefined)
      setItems(res.data.items); setTotal(res.data.total)
      setMeta({fuente:res.data.fuente, factor:res.data.factor_region, nombre:res.data.nombre_region})
      setCats(res.data.categorias||[])
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(()=>{ load() }, [region, cat])
  useEffect(()=>{ const t = setTimeout(()=>load(), 400); return ()=>clearTimeout(t) }, [q])

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col border border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-navy-50 rounded-xl flex items-center justify-center">
              <Database size={19} className="text-navy-600"/>
            </div>
            <div>
              <h2 className="font-bold text-slate-800">Base de datos APU 2026</h2>
              <p className="text-xs text-slate-400">Escuela de Contratistas · {meta.nombre} · Factor ×{meta.factor}</p>
            </div>
          </div>
          <button onClick={onClose} className="btn-ghost p-2 rounded-xl"><X size={18}/></button>
        </div>

        {/* Info bar */}
        <div className="px-5 py-2 bg-navy-50 border-b border-navy-100 flex items-center justify-between">
          <span className="text-xs text-navy-700 font-medium">{meta.fuente}</span>
          <span className="badge badge-navy">{total.toLocaleString('es-CO')} actividades encontradas</span>
        </div>

        {/* Filtros */}
        <div className="flex gap-3 p-4 border-b border-slate-100">
          <div className="flex-1 relative">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"/>
            <input className="input pl-10 text-sm" placeholder="Buscar por descripción, código o perfil..."
              value={q} onChange={e=>setQ(e.target.value)}/>
          </div>
          <select className="select text-sm w-56" value={cat} onChange={e=>setCat(e.target.value)}>
            <option value="">Todas las categorías</option>
            {cats.map(c=><option key={c} value={c}>{CAT_ICONS[c]||'📦'} {c}</option>)}
          </select>
        </div>

        {/* Tabla */}
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-40 text-slate-400 gap-3">
              <Loader2 size={24} className="animate-spin text-navy-400"/>
              <p className="text-sm">Cargando precios APU 2026...</p>
            </div>
          ) : (
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white z-10">
                <tr className="text-slate-400 border-b border-slate-100">
                  <th className="text-left py-2.5 px-2 font-semibold w-20">Código</th>
                  <th className="text-left py-2.5 px-2 font-semibold">Descripción</th>
                  <th className="text-center py-2.5 px-2 font-semibold w-16">Und.</th>
                  <th className="text-right py-2.5 px-2 font-semibold w-36">Precio ({meta.nombre})</th>
                  <th className="text-left py-2.5 px-2 font-semibold w-36">Categoría</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item,i)=>(
                  <tr key={item.codigo} className={clsx(
                    'border-b border-slate-50 hover:bg-slate-50 transition-colors',
                    i%2===0?'':'bg-slate-50/30'
                  )}>
                    <td className="py-2 px-2 font-mono text-slate-500 font-semibold">{item.codigo}</td>
                    <td className="py-2 px-2 text-slate-700">{item.descripcion}</td>
                    <td className="py-2 px-2 text-center text-slate-500">{item.unidad}</td>
                    <td className="py-2 px-2 text-right font-bold text-slate-800">{COP(item.precio)}</td>
                    <td className="py-2 px-2">
                      <span className="badge badge-slate text-[10px]">
                        {CAT_ICONS[item.categoria]||'📦'} {item.categoria}
                      </span>
                    </td>
                  </tr>
                ))}
                {items.length===0 && (
                  <tr><td colSpan={5} className="text-center py-12 text-slate-400">
                    <p className="text-2xl mb-2">🔍</p>
                    No se encontraron actividades con ese criterio
                  </td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
        <div className="p-3 border-t border-slate-100 text-xs text-slate-400 text-center bg-slate-50/50 rounded-b-2xl">
          Precios incluyen: materiales + mano de obra + herramientas y equipos · Fuente: {meta.fuente}
        </div>
      </div>
    </div>
  )
}

function clsx(...args) { return args.filter(Boolean).join(' ') }
