import React from 'react'
import { Package, Hammer, Truck, Users } from 'lucide-react'
import { COP } from '../../utils/format'

export default function DesglosePanel({ desglose, flete }) {
  if (!desglose && !flete) return null

  return (
    <div className="space-y-4">
      {desglose && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Package className="w-4 h-4 text-blue-600" />
            Desglose APU: Material / Mano de Obra / Equipo
          </h3>

          {/* Barra de composicion */}
          <div className="h-8 rounded-lg overflow-hidden flex mb-3">
            <div
              className="bg-blue-600 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${desglose.pct_material}%` }}
            >
              {desglose.pct_material > 15 && `${desglose.pct_material}%`}
            </div>
            <div
              className="bg-emerald-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${desglose.pct_mano_obra}%` }}
            >
              {desglose.pct_mano_obra > 15 && `${desglose.pct_mano_obra}%`}
            </div>
            <div
              className="bg-amber-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${desglose.pct_equipo}%` }}
            >
              {desglose.pct_equipo > 8 && `${desglose.pct_equipo}%`}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-xs text-blue-700 font-medium mb-1">Material</div>
              <div className="text-sm font-bold text-blue-900">{COP(desglose.total_material)}</div>
            </div>
            <div className="bg-emerald-50 rounded-lg p-3">
              <div className="text-xs text-emerald-700 font-medium mb-1">Mano de obra</div>
              <div className="text-sm font-bold text-emerald-900">{COP(desglose.total_mano_obra)}</div>
            </div>
            <div className="bg-amber-50 rounded-lg p-3">
              <div className="text-xs text-amber-700 font-medium mb-1">Equipo</div>
              <div className="text-sm font-bold text-amber-900">{COP(desglose.total_equipo)}</div>
            </div>
          </div>

          {desglose.dias_cuadrilla_estimados > 0 && (
            <div className="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 rounded-lg p-3">
              <Users className="w-4 h-4 text-slate-400" />
              <span>
                <strong>{desglose.dias_cuadrilla_estimados.toLocaleString('es-CO')}</strong> días-cuadrilla
                estimados (jornal promedio ${desglose.jornal_referencia?.cuadrilla_promedio?.toLocaleString('es-CO')}/día)
              </span>
            </div>
          )}

          <p className="text-xs text-slate-400 mt-3">{desglose.nota}</p>
        </div>
      )}

      {flete && flete.factor_flete > 1.0 && (
        <div className="bg-white rounded-xl border border-orange-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
            <Truck className="w-4 h-4 text-orange-600" />
            Flete: {flete.region}
          </h3>
          <div className="flex items-center gap-4 mb-2">
            <div className="text-2xl font-bold text-orange-600">
              ×{flete.factor_flete.toFixed(3)}
            </div>
            <div className="text-sm text-slate-600">
              sobre el costo de materiales
              {flete.recargo_materiales_pct && ` (~${flete.recargo_materiales_pct}% recargo)`}
            </div>
          </div>
          <p className="text-sm text-slate-500">{flete.nota}</p>
          {flete.requiere_cotizacion_especial && (
            <div className="mt-3 text-xs bg-orange-50 text-orange-700 rounded-lg p-2 font-medium">
              ⚠ Distancia/acceso especial — solicitar cotización real de transporte antes de licitar
            </div>
          )}
        </div>
      )}
    </div>
  )
}
