import React from 'react'
import { AlertTriangle, CheckCircle, XCircle, Info, Shield } from 'lucide-react'
import { clsx } from 'clsx'

const SEV_CONFIG = {
  ERROR:       { icon: XCircle,      cls: 'text-red-700 bg-red-50 border-red-200',    label: 'Error NSR-10' },
  ADVERTENCIA: { icon: AlertTriangle, cls: 'text-amber-700 bg-amber-50 border-amber-200', label: 'Advertencia' },
  INFO:        { icon: Info,          cls: 'text-blue-700 bg-blue-50 border-blue-100',  label: 'Info' },
}

export default function NSR10Panel({ alertas = [], correcciones = [], puntuacion }) {
  if (!alertas || alertas.length === 0) return null

  const errores = alertas.filter(a => a.severidad === 'ERROR' || a.includes?.('[C.') && !a.includes('INFO'))
  const todos = alertas.slice(0, 8)

  const scoreColor = puntuacion >= 90 ? 'text-emerald-600' : puntuacion >= 70 ? 'text-amber-600' : 'text-red-600'
  const scoreBg   = puntuacion >= 90 ? 'bg-emerald-50 border-emerald-200' : puntuacion >= 70 ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200'

  return (
    <div className={clsx('rounded-2xl border p-4 space-y-3', scoreBg)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={16} className={scoreColor}/>
          <span className={clsx('text-sm font-bold', scoreColor)}>Validación NSR-10</span>
        </div>
        {puntuacion !== undefined && (
          <div className={clsx('text-sm font-bold px-3 py-1 rounded-lg', scoreColor, scoreBg)}>
            {puntuacion.toFixed(0)}/100
          </div>
        )}
      </div>

      <div className="space-y-2">
        {todos.map((alerta, i) => {
          const textoAlerta = typeof alerta === 'string' ? alerta : alerta.mensaje
          const sev = typeof alerta === 'object' ? alerta.severidad : 
            alerta.includes('ERROR') ? 'ERROR' : alerta.includes('[C.') ? 'ADVERTENCIA' : 'INFO'
          const cfg = SEV_CONFIG[sev] || SEV_CONFIG.INFO
          const Ic = cfg.icon
          return (
            <div key={i} className={clsx('flex items-start gap-2 p-2.5 rounded-xl border text-xs', cfg.cls)}>
              <Ic size={13} className="shrink-0 mt-0.5"/>
              <span className="leading-relaxed">{textoAlerta}</span>
            </div>
          )
        })}
        {alertas.length > 8 && (
          <p className="text-xs text-slate-400 text-center">
            +{alertas.length - 8} alertas adicionales — ver detalle en reporte
          </p>
        )}
      </div>

      {correcciones?.length > 0 && (
        <div className="pt-2 border-t border-current/10">
          <p className="text-xs font-semibold mb-1.5 flex items-center gap-1">
            <CheckCircle size={12}/> Correcciones sugeridas:
          </p>
          {correcciones.slice(0,3).map((c,i)=>(
            <p key={i} className="text-xs pl-4 mb-1">• {c}</p>
          ))}
        </div>
      )}
    </div>
  )
}
