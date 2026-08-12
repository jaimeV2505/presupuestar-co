import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Building2 } from 'lucide-react'
import { recuperarAPI } from '../services/api'

export default function Restablecer() {
  const nav = useNavigate()
  const params = new URLSearchParams(window.location.search)
  const email = params.get('email') || ''
  const token = params.get('token') || ''
  const [p1, setP1] = useState('')
  const [p2, setP2] = useState('')
  const [loading, setLoading] = useState(false)
  const [listo, setListo] = useState(false)

  const enlaceValido = email && token

  const submit = async (e) => {
    e.preventDefault()
    if (p1.length < 8) { toast.error('Mínimo 8 caracteres'); return }
    if (p1 !== p2) { toast.error('Las contraseñas no coinciden'); return }
    setLoading(true)
    try {
      await recuperarAPI.restablecer({ email, token, password: p1 })
      setListo(true)
      toast.success('¡Contraseña actualizada!')
      setTimeout(() => nav('/login'), 2500)
    } catch (err) {
      toast.error(err.message || 'El enlace no es válido o ya expiró')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 text-navy-700">
            <Building2 className="w-6 h-6" />
            <span className="font-black text-lg">PresupuestarCO</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          {!enlaceValido ? (
            <div className="text-center">
              <p className="text-sm font-semibold text-slate-700 mb-1">Enlace incompleto</p>
              <p className="text-xs text-slate-400 mb-4">
                Abre el enlace completo desde el correo que te enviamos, o pide uno nuevo.
              </p>
              <Link to="/login" className="text-sm text-navy-600 font-medium">← Volver</Link>
            </div>
          ) : listo ? (
            <div className="text-center">
              <p className="text-3xl mb-2">✅</p>
              <p className="text-sm font-semibold text-slate-700">Contraseña actualizada</p>
              <p className="text-xs text-slate-400 mt-1">Redirigiendo al inicio de sesión...</p>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-3">
              <h1 className="text-base font-bold text-slate-800">Crea tu nueva contraseña</h1>
              <p className="text-[11px] text-slate-400 -mt-1">Para la cuenta {email}</p>
              <input className="input" type="password" placeholder="Nueva contraseña (mínimo 8)"
                     value={p1} onChange={e => setP1(e.target.value)} autoComplete="new-password" autoFocus />
              <input className="input" type="password" placeholder="Repítela"
                     value={p2} onChange={e => setP2(e.target.value)} autoComplete="new-password" />
              <button disabled={loading}
                      className="w-full bg-navy-600 hover:bg-navy-700 text-white font-semibold rounded-xl py-3 transition disabled:opacity-50">
                {loading ? 'Guardando...' : 'Guardar y entrar'}
              </button>
              <p className="text-[10px] text-slate-300 text-center">El enlace vale 30 minutos y se usa una sola vez</p>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
