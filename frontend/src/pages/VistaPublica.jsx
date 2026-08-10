import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { CheckCircle2, ChevronDown, ChevronUp, Phone, Building2 } from 'lucide-react'
import { shareAPI } from '../services/api'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

export default function VistaPublica() {
  const { token } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [abiertos, setAbiertos] = useState({})
  const [aceptando, setAceptando] = useState(false)
  const [aceptado, setAceptado] = useState(false)
  const [rechazado, setRechazado] = useState(false)

  useEffect(() => {
    shareAPI.verPublico(token)
      .then(d => {
        setData(d)
        setAceptado(d.estado === 'aceptado')
        setRechazado(d.estado === 'rechazado')
        // Abrir el primer capitulo por defecto
        const caps = Object.keys(d.capitulos || {})
        if (caps.length) setAbiertos({ [caps[0]]: true })
      })
      .catch(e => setError(e.message))
  }, [token])

  const rechazar = async () => {
    if (!confirm('¿Deseas rechazar este presupuesto? El contratista será notificado.')) return
    try {
      await shareAPI.rechazar(token)
      setRechazado(true)
    } catch (e) { alert(e.message) }
  }

  const aceptar = async () => {
    if (!confirm('¿Confirmas que aceptas este presupuesto?')) return
    setAceptando(true)
    try {
      await shareAPI.aceptar(token)
      setAceptado(true)
    } catch (e) { alert(e.message) }
    finally { setAceptando(false) }
  }

  if (error) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-center">
      <div>
        <p className="text-slate-600 font-medium">{error}</p>
        <p className="text-sm text-slate-400 mt-2">Verifica el enlace o pide uno nuevo al contratista.</p>
      </div>
    </div>
  )

  if (!data) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400">
      Cargando presupuesto...
    </div>
  )

  const t = data.totales
  const c = data.contratista

  return (
    <div className="min-h-screen bg-slate-100 pb-28">
      {/* Header del contratista */}
      <div className="bg-navy-800 text-white px-5 pt-8 pb-12">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center gap-3 mb-6">
            {c.logo_b64 ? (
              <img src={c.logo_b64} alt="" className="w-12 h-12 rounded-xl object-contain bg-white p-1" />
            ) : (
              <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                <Building2 className="w-6 h-6" />
              </div>
            )}
            <div>
              <p className="font-semibold">{c.empresa || c.nombre}</p>
              {c.empresa && <p className="text-xs text-blue-200">{c.nombre}</p>}
            </div>
          </div>
          <p className="text-blue-200 text-xs uppercase tracking-wide mb-1">Presupuesto de obra</p>
          <h1 className="text-xl font-bold leading-tight">{data.proyecto}</h1>
          {data.cliente && <p className="text-sm text-blue-200 mt-1">Para: {data.cliente}</p>}
          {data.direccion && <p className="text-xs text-blue-300">{data.direccion}</p>}
          <p className="text-xs text-blue-300 mt-2">Fecha: {data.fecha}</p>
        </div>
      </div>

      {/* Total destacado */}
      <div className="max-w-lg mx-auto px-4 -mt-6">
        <div className="bg-white rounded-2xl shadow-lg p-5 text-center">
          <p className="text-xs text-slate-400 uppercase tracking-wide">Valor total</p>
          <p className="text-3xl font-black text-slate-800 mt-1">{COP(t.total)}</p>
          {aceptado && (
            <span className="inline-flex items-center gap-1.5 mt-2 text-sm text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full font-medium">
              <CheckCircle2 className="w-4 h-4" /> Presupuesto aceptado
            </span>
          )}
          {rechazado && !aceptado && (
            <span className="inline-flex items-center gap-1.5 mt-2 text-sm text-red-600 bg-red-50 px-3 py-1 rounded-full font-medium">
              Presupuesto rechazado
            </span>
          )}
        </div>
      </div>

      {/* Capitulos */}
      <div className="max-w-lg mx-auto px-4 mt-4 space-y-2">
        {Object.entries(data.capitulos || {}).map(([cap, info]) => (
          <div key={cap} className="bg-white rounded-xl overflow-hidden">
            <button onClick={() => setAbiertos(a => ({ ...a, [cap]: !a[cap] }))}
                    className="w-full flex items-center justify-between p-4">
              <div className="text-left">
                <p className="text-sm font-semibold text-slate-700">{cap.charAt(0) + cap.slice(1).toLowerCase()}</p>
                <p className="text-xs text-slate-400">{info.items.length} ítem{info.items.length !== 1 ? 's' : ''}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-slate-800">{COP(info.subtotal)}</span>
                {abiertos[cap] ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </div>
            </button>
            {abiertos[cap] && (
              <div className="border-t border-slate-100 divide-y divide-slate-50">
                {info.items.map((it, i) => (
                  <div key={i} className="px-4 py-2.5 flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-xs text-slate-600 leading-snug">{it.descripcion}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {it.cantidad} {it.unidad} × {COP(it.precio_unitario)}
                      </p>
                    </div>
                    <span className="text-xs font-medium text-slate-700 shrink-0">{COP(it.precio_total)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Resumen financiero */}
      <div className="max-w-lg mx-auto px-4 mt-4">
        <div className="bg-white rounded-xl p-4 space-y-2 text-sm">
          <div className="flex justify-between text-slate-600">
            <span>Costo directo</span><span>{COP(t.subtotal_directo)}</span>
          </div>
          {t.aiu_total > 0 && (
            <>
              <div className="flex justify-between text-slate-500 text-xs">
                <span>Administración ({t.admin_pct}%)</span><span>{COP(t.admin_valor)}</span>
              </div>
              <div className="flex justify-between text-slate-500 text-xs">
                <span>Imprevistos ({t.imprevistos_pct}%)</span><span>{COP(t.imprevistos_valor)}</span>
              </div>
              <div className="flex justify-between text-slate-500 text-xs">
                <span>Utilidad ({t.utilidad_pct}%)</span><span>{COP(t.utilidad_valor)}</span>
              </div>
            </>
          )}
          <div className="flex justify-between text-slate-600">
            <span>IVA</span><span>{COP(t.iva)}</span>
          </div>
          <div className="flex justify-between font-bold text-slate-800 pt-2 border-t border-slate-100">
            <span>Total</span><span>{COP(t.total)}</span>
          </div>
          <p className="text-[10px] text-slate-400 pt-1">{t.regimen_iva}</p>
        </div>

        {data.notas && (
          <div className="bg-white rounded-xl p-4 mt-2 text-xs text-slate-500 whitespace-pre-wrap">
            {data.notas}
          </div>
        )}

        {c.condiciones && (
          <div className="bg-white rounded-xl p-4 mt-2">
            <p className="text-xs font-semibold text-slate-600 mb-2">Condiciones</p>
            <p className="text-[11px] text-slate-400 whitespace-pre-wrap leading-relaxed">{c.condiciones}</p>
          </div>
        )}

        <p className="text-center text-[10px] text-slate-400 mt-4">
          Hecho con PresupuestarCO
        </p>
      </div>

      {/* Barra de accion fija */}
      {!aceptado && !rechazado && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4">
          <div className="max-w-lg mx-auto space-y-2">
          <div className="flex gap-2">
            {c.telefono && (
              <a href={`https://wa.me/57${c.telefono.replace(/\D/g, '')}`}
                 className="flex items-center justify-center gap-2 flex-1 py-3 rounded-xl border border-slate-200 text-sm font-medium text-slate-600">
                <Phone className="w-4 h-4" /> Preguntar
              </a>
            )}
            <button onClick={aceptar} disabled={aceptando}
                    className="flex items-center justify-center gap-2 flex-[2] py-3 rounded-xl bg-emerald-500 text-white text-sm font-bold disabled:opacity-50">
              <CheckCircle2 className="w-4 h-4" />
              {aceptando ? 'Confirmando...' : 'Aceptar presupuesto'}
            </button>
          </div>
          <button onClick={rechazar} className="w-full text-center text-[11px] text-slate-400 py-1">
            No me interesa este presupuesto
          </button>
          </div>
        </div>
      )}
    </div>
  )
}
