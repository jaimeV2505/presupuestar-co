import React, { useState, useEffect } from 'react'
import { X, Ruler, Package, ChevronDown } from 'lucide-react'
import axios from 'axios'
import { COP, NUM } from '../../utils/format'

const api = axios.create({ baseURL: '/api', timeout: 10000 })

const TABS = [
  { id: 'varillas', label: '🔩 Varillas acero', icon: Ruler },
  { id: 'concreto', label: '🏛 Dosif. concreto', icon: Package },
]

export default function TablasModal({ onClose }) {
  const [tab, setTab] = useState('varillas')
  const [varillas, setVarillas] = useState([])
  const [dosif, setDosif] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/precios/varillas'),
      api.get('/precios/dosificacion-concreto?fc_mpa=20.7'),
    ]).then(([rv, rc]) => {
      setVarillas(rv.data.varillas || [])
      setDosif(rc.data.tabla_completa || [])
    }).catch(console.error)
    .finally(() => setLoading(false))
  }, [])

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col border border-slate-200">
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <div>
            <h2 className="font-bold text-slate-800">Tablas técnicas de materiales</h2>
            <p className="text-xs text-slate-400 mt-0.5">Datos reales para cálculo preciso de cantidades</p>
          </div>
          <button onClick={onClose} className="btn-ghost p-2 rounded-xl"><X size={18}/></button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-3 border-b border-slate-100 bg-slate-50">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                tab === t.id ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-slate-400">Cargando...</div>
          ) : tab === 'varillas' ? (
            <>
              <p className="text-xs text-slate-500 mb-3 p-3 bg-blue-50 rounded-xl border border-blue-100">
                Pesos reales según tabla de caracterización de varilla. Usados para calcular kg de acero
                cuando el plano especifica la varilla exacta (ej: 4Ø5/8", #5@15cm).
              </p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-100 text-xs">
                    <th className="text-left py-2 font-medium"># Varilla</th>
                    <th className="text-center py-2 font-medium">Diámetro [Pulg]</th>
                    <th className="text-center py-2 font-medium">Diámetro [mm]</th>
                    <th className="text-right py-2 font-medium">Sección [cm²]</th>
                    <th className="text-right py-2 font-medium font-bold text-slate-700">Peso [kg/m]</th>
                  </tr>
                </thead>
                <tbody>
                  {varillas.map((v, i) => (
                    <tr key={v.numero} className={`border-b border-slate-50 ${i%2===0?'':'bg-slate-50/50'}`}>
                      <td className="py-2.5 font-bold text-navy-600">#{v.numero}</td>
                      <td className="py-2.5 text-center text-slate-600">{v.pulg}"</td>
                      <td className="py-2.5 text-center text-slate-600">{v.mm}</td>
                      <td className="py-2.5 text-right text-slate-600">{v.area_cm2}</td>
                      <td className="py-2.5 text-right font-bold text-slate-800">{v.peso_kg_m}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <>
              <p className="text-xs text-slate-500 mb-3 p-3 bg-amber-50 rounded-xl border border-amber-100">
                Dosificación de concreto según resistencia. Cantidades por m³. Cemento: saco 42.5 kg.
                El motor usa esta tabla para calcular materiales exactos por volumen de concreto.
              </p>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-100">
                    <th className="text-left py-2 font-medium">Proporción</th>
                    <th className="text-center py-2 font-medium">kg/cm²</th>
                    <th className="text-center py-2 font-medium">PSI</th>
                    <th className="text-center py-2 font-medium font-bold text-slate-700">MPa</th>
                    <th className="text-right py-2 font-medium">Cemento (cmt)</th>
                    <th className="text-right py-2 font-medium">Arena m³</th>
                    <th className="text-right py-2 font-medium">Grava m³</th>
                    <th className="text-right py-2 font-medium">Agua lts</th>
                  </tr>
                </thead>
                <tbody>
                  {dosif.map((d, i) => (
                    <tr key={d.proporcion} className={`border-b border-slate-50 ${i%2===0?'':'bg-slate-50/50'}`}>
                      <td className="py-2 font-mono font-semibold text-slate-700">{d.proporcion}</td>
                      <td className="py-2 text-center text-slate-600">{d.kg_cm2}</td>
                      <td className="py-2 text-center text-slate-600">{d.psi}</td>
                      <td className="py-2 text-center font-bold text-navy-600">{d.mpa}</td>
                      <td className="py-2 text-right text-slate-600">{d.cemento_sacos !== undefined ? `${(d.cemento_sacos).toFixed(1)} sacos` : '-'}</td>
                      <td className="py-2 text-right text-slate-600">{d.arena_m3}</td>
                      <td className="py-2 text-right text-slate-600">{d.grava_m3}</td>
                      <td className="py-2 text-right text-slate-600">{d.agua_lts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>

        <div className="p-3 border-t border-slate-100 text-xs text-slate-400 text-center bg-slate-50/50 rounded-b-2xl">
          Fuente: Tablas de caracterización de varilla y dosificación de concreto — Colombia
        </div>
      </div>
    </div>
  )
}
