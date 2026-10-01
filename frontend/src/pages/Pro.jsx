import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, CheckCircle2, Crown, Clock } from 'lucide-react'
import { pagosAPI, soporteAPI } from '../services/api'

const BENEFICIOS = [
  'Presupuestos ILIMITADOS — cotiza todo lo que tu negocio necesite',
  'Todas las funciones que ya conoces, sin tope',
  'Soporte prioritario',
  'Apoyas una herramienta hecha en Colombia para contratistas 🇨🇴',
]

export default function Pro() {
  const nav = useNavigate()
  const [info, setInfo] = useState(null)
  const [mensaje, setMensaje] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)

  useEffect(() => {
    pagosAPI.info().then(setInfo).catch(e => toast.error(e.message))
  }, [])

  const pedirAcceso = async () => {
    setEnviando(true)
    try {
      await soporteAPI.crear({
        asunto: 'Quiero más presupuestos',
        descripcion: mensaje.trim() || '(sin mensaje adicional)',
        contexto: `pagina: /pro · plan: ${info?.plan || '?'}`,
      })
      setEnviado(true)
      toast.success('¡Listo! Te escribimos pronto para darte más acceso')
    } catch (e) { toast.error(e.response?.data?.detail || e.message) }
    finally { setEnviando(false) }
  }

  if (!info) return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400">Cargando...</div>

  const esPro = info.plan === 'pro'

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
            <p className="text-blue-200 text-sm mt-2">Presupuestos ilimitados, sin tope</p>
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

        {/* Durante el lanzamiento: acceso gratis + pedir mas por soporte */}
        {!esPro && (
          <div className="bg-white rounded-2xl border-2 border-emerald-300 p-5 relative">
            <span className="absolute -top-3 left-4 bg-emerald-500 text-white text-[9px] font-black uppercase tracking-wider px-3 py-1 rounded-full">
              🚀 Fase de lanzamiento
            </span>
            <h3 className="text-sm font-semibold text-slate-700 mb-1 mt-1">
              Durante el lanzamiento, el acceso es gratis
            </h3>
            <p className="text-[12px] text-slate-500 mb-4">
              Tenés 5 presupuestos gratis para probar todo a fondo. ¿Necesitás más?
              Contanos y te damos acceso sin costo mientras seguimos en esta fase.
            </p>
            {enviado ? (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
                <Clock className="w-6 h-6 text-emerald-500 mx-auto mb-1" />
                <p className="text-sm font-semibold text-emerald-700">Recibimos tu pedido</p>
                <p className="text-[11px] text-emerald-600 mt-1">Te contactamos pronto para activar tu acceso.</p>
              </div>
            ) : (
              <>
                <textarea className="input min-h-[80px] text-sm mb-3"
                          placeholder="Contanos un poco de tu negocio o qué necesitás (opcional)"
                          value={mensaje} onChange={e => setMensaje(e.target.value)} />
                <button onClick={pedirAcceso} disabled={enviando}
                        className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold transition disabled:opacity-50">
                  {enviando ? 'Enviando...' : '🔓 Pedir más acceso'}
                </button>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

