import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, CheckCircle2, Crown, Clock, Copy } from 'lucide-react'
import { pagosAPI } from '../services/api'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

const BENEFICIOS = [
  'Presupuestos ilimitados',
  'Tu logo en PDFs y enlaces — sin marca de agua',
  'Contrato de Ejecución de Obra Civil con firma digital',
  'Avances de obra con valor ejecutado y fotos',
  'Encuestas de satisfacción y calificaciones ⭐',
  'Soporte prioritario por WhatsApp',
]

export default function Pro() {
  const nav = useNavigate()
  const [info, setInfo] = useState(null)
  const [solicitud, setSolicitud] = useState(null)
  const [metodo, setMetodo] = useState('nequi')
  const [referencia, setReferencia] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    pagosAPI.info().then(setInfo).catch(e => toast.error(e.message))
    pagosAPI.miSolicitud().then(setSolicitud).catch(() => {})
  }, [])

  const copiar = (txt) => { navigator.clipboard.writeText(txt); toast.success('Copiado') }

  const reportarPago = async () => {
    setEnviando(true)
    try {
      const res = await pagosAPI.solicitar({ metodo, referencia })
      toast.success(res.mensaje)
      setSolicitud({ existe: true, estado: 'pendiente' })
    } catch (e) { toast.error(e.message) }
    finally { setEnviando(false) }
  }

  if (!info) return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400">Cargando...</div>

  const esPro = info.plan === 'pro'
  const pendiente = solicitud?.existe && solicitud.estado === 'pendiente'

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={() => nav('/')} className="p-2 hover:bg-slate-100 rounded-lg">
            <ArrowLeft className="w-4 h-4 text-slate-600" />
          </button>
          <h1 className="font-semibold text-slate-800">Plan Pro</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Estado actual */}
        {esPro ? (
          <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl p-6 text-white text-center mb-6">
            <Crown className="w-10 h-10 mx-auto mb-2" />
            <h2 className="text-xl font-black">¡Eres Pro! 🎉</h2>
            <p className="text-emerald-100 text-sm mt-1">
              Tu plan está activo{info.plan_vence ? ` hasta el ${info.plan_vence}` : ''}
            </p>
          </div>
        ) : (
          <div className="bg-gradient-to-br from-navy-800 to-navy-600 rounded-2xl p-6 text-white text-center mb-6">
            <Crown className="w-10 h-10 mx-auto mb-2 text-amber-400" />
            <h2 className="text-2xl font-black">PresupuestarCO Pro</h2>
            <div className="flex items-end justify-center gap-2 mt-2">
              <span className="text-4xl font-black">{COP(info.precio_pro)}</span>
              <span className="text-blue-200 pb-1.5">/mes</span>
            </div>
          </div>
        )}

        {/* Beneficios */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Lo que incluye</h3>
          <ul className="space-y-2.5">
            {BENEFICIOS.map((b, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-slate-600">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>

        {!esPro && (
          pendiente ? (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-center">
              <Clock className="w-8 h-8 text-amber-500 mx-auto mb-2" />
              <h3 className="font-semibold text-amber-800">Pago en verificación</h3>
              <p className="text-sm text-amber-700 mt-1">
                Recibimos tu reporte. Activamos tu plan Pro en menos de 24 horas
                y te avisamos por WhatsApp.
              </p>
            </div>
          ) : (
            <>
              {/* Paso 1: pagar */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-4">
                <h3 className="text-sm font-semibold text-slate-700 mb-1">
                  <span className="inline-flex items-center justify-center w-5 h-5 bg-navy-600 text-white rounded-full text-[10px] font-bold mr-1.5">1</span>
                  Realiza el pago de {COP(info.precio_pro)}
                </h3>
                <p className="text-[11px] text-slate-400 mb-4">Elige el método que prefieras:</p>

                <div className="space-y-2.5">
                  {info.nequi && (
                    <button onClick={() => { setMetodo('nequi'); copiar(info.nequi) }}
                            className={`w-full flex items-center justify-between rounded-xl border-2 p-3.5 transition ${metodo === 'nequi' ? 'border-emerald-400 bg-emerald-50' : 'border-slate-200'}`}>
                      <div className="text-left">
                        <p className="text-sm font-semibold text-slate-700">Nequi</p>
                        <p className="text-xs text-slate-500">{info.nequi}</p>
                      </div>
                      <Copy className="w-4 h-4 text-slate-400" />
                    </button>
                  )}
                  {info.banco && (
                    <button onClick={() => { setMetodo('bancolombia'); copiar(info.banco) }}
                            className={`w-full flex items-center justify-between rounded-xl border-2 p-3.5 transition ${metodo === 'bancolombia' ? 'border-emerald-400 bg-emerald-50' : 'border-slate-200'}`}>
                      <div className="text-left">
                        <p className="text-sm font-semibold text-slate-700">Bancolombia</p>
                        <p className="text-xs text-slate-500">{info.banco}</p>
                      </div>
                      <Copy className="w-4 h-4 text-slate-400" />
                    </button>
                  )}
                  {!info.nequi && !info.banco && (
                    <p className="text-xs text-amber-600 bg-amber-50 rounded-lg p-3">
                      Los datos de pago aún no están configurados. Escríbenos por WhatsApp para activar tu Pro.
                    </p>
                  )}
                </div>
              </div>

              {/* Paso 2: reportar */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5">
                <h3 className="text-sm font-semibold text-slate-700 mb-1">
                  <span className="inline-flex items-center justify-center w-5 h-5 bg-navy-600 text-white rounded-full text-[10px] font-bold mr-1.5">2</span>
                  Reporta tu pago
                </h3>
                <p className="text-[11px] text-slate-400 mb-3">
                  Verificamos y activamos tu Pro en menos de 24 horas.
                </p>
                <input className="input mb-3" placeholder="Nº de comprobante o referencia (opcional)"
                       value={referencia} onChange={e => setReferencia(e.target.value)} />
                <button onClick={reportarPago} disabled={enviando}
                        className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold transition disabled:opacity-50">
                  {enviando ? 'Enviando...' : '✓ Ya pagué — activar mi Pro'}
                </button>
              </div>
            </>
          )
        )}
      </main>
    </div>
  )
}
