import React, { useState, useEffect } from 'react'
import { TrendingUp, AlertTriangle } from 'lucide-react'
import { COP } from '../../utils/format'
import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 10000 })

export default function SensibilidadPanel({ items = [], total = 0 }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    if (!items.length || !total) return
    // Calcular sensibilidad localmente
    const acero   = items.filter(i => i.nombre?.toLowerCase().includes('acero') || i.capitulo?.includes('METAL')).reduce((s,i)=>s+i.precio_total,0)
    const concreto = items.filter(i => i.nombre?.toLowerCase().includes('concreto')).reduce((s,i)=>s+i.precio_total,0)
    const metal    = items.filter(i => i.capitulo === 'ESTRUCTURA METÁLICA').reduce((s,i)=>s+i.precio_total,0)

    setData({
      distribucion: {
        acero:    total ? (acero/total*100).toFixed(1) : 0,
        concreto: total ? (concreto/total*100).toFixed(1) : 0,
        metalica: total ? (metal/total*100).toFixed(1) : 0,
      },
      escenarios: [
        { material: 'Acero', alza: 10, impacto: Math.round(acero*0.10), pct: (acero*0.10/total*100).toFixed(1) },
        { material: 'Cemento', alza: 15, impacto: Math.round(concreto*0.08), pct: (concreto*0.08/total*100).toFixed(1) },
        { material: 'Metálica', alza: 10, impacto: Math.round(metal*0.10), pct: (metal*0.10/total*100).toFixed(1) },
      ].filter(e => e.impacto > 0)
    })
  }, [items.length, total])

  if (!data || data.escenarios.length === 0) return null

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={16} className="text-amber-500"/>
        <h3 className="text-sm font-bold text-slate-700">Análisis de sensibilidad de precios</h3>
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Impacto sobre el presupuesto si los materiales suben de precio:
      </p>
      <div className="space-y-2">
        {data.escenarios.map((e,i) => (
          <div key={i} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl border border-slate-100">
            <div>
              <span className="text-xs font-semibold text-slate-700">{e.material} +{e.alza}%</span>
              <span className="text-xs text-slate-400 ml-2">({e.pct}% del total)</span>
            </div>
            <span className="text-xs font-bold text-amber-700">+{COP(e.impacto)}</span>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-slate-400 mt-3 flex items-start gap-1">
        <AlertTriangle size={11} className="shrink-0 mt-0.5"/>
        Si la obra dura más de 3 meses, incluir cláusula de reajuste en el contrato.
      </p>
    </div>
  )
}
