import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Building2 } from 'lucide-react'
import { authAPI } from '../services/api'

export default function Login({ modo = 'login' }) {
  const nav = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', nombre: '', empresa: '', telefono: '' })
  const [loading, setLoading] = useState(false)
  const esRegistro = modo === 'registro'

  const submit = async (e) => {
    e.preventDefault()
    if (!form.email || !form.password) { toast.error('Email y contraseña requeridos'); return }
    if (esRegistro && !form.nombre) { toast.error('Tu nombre es requerido'); return }
    setLoading(true)
    try {
      const res = esRegistro
        ? await authAPI.registro(form)
        : await authAPI.login({ email: form.email, password: form.password })
      localStorage.setItem('token', res.token)
      localStorage.setItem('usuario', JSON.stringify(res.usuario))
      toast.success(esRegistro ? '¡Bienvenido a PresupuestarCO!' : `Hola, ${res.usuario.nombre}`)
      nav('/')
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-navy-800 to-navy-600 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-white/10 rounded-2xl mb-3">
            <Building2 className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">PresupuestarCO</h1>
          <p className="text-blue-200 text-sm mt-1">Presupuestos de obra profesionales en minutos</p>
        </div>

        <form onSubmit={submit} className="bg-white rounded-2xl shadow-2xl p-6 space-y-4">
          <h2 className="font-semibold text-slate-800">
            {esRegistro ? 'Crea tu cuenta gratis' : 'Inicia sesión'}
          </h2>

          {esRegistro && (
            <>
              <input className="input" placeholder="Tu nombre *" value={form.nombre} onChange={set('nombre')} />
              <input className="input" placeholder="Empresa (opcional)" value={form.empresa} onChange={set('empresa')} />
              <input className="input" placeholder="WhatsApp (ej: 300 123 4567)" value={form.telefono} onChange={set('telefono')} />
            </>
          )}

          <input className="input" type="email" placeholder="Email *" value={form.email} onChange={set('email')} autoComplete="email" />
          <input className="input" type="password" placeholder={esRegistro ? 'Contraseña (mínimo 8 caracteres) *' : 'Contraseña *'}
                 value={form.password} onChange={set('password')} autoComplete={esRegistro ? 'new-password' : 'current-password'} />

          <button disabled={loading}
                  className="w-full bg-navy-600 hover:bg-navy-700 text-white font-semibold rounded-xl py-3 transition disabled:opacity-50">
            {loading ? 'Un momento...' : esRegistro ? 'Crear cuenta gratis' : 'Entrar'}
          </button>

          <p className="text-center text-sm text-slate-500">
            {esRegistro ? (
              <>¿Ya tienes cuenta? <Link to="/login" className="text-navy-600 font-medium">Inicia sesión</Link></>
            ) : (
              <>¿Primera vez? <Link to="/registro" className="text-navy-600 font-medium">Crea tu cuenta gratis</Link></>
            )}
          </p>
          {esRegistro && (
            <p className="text-xs text-slate-400 text-center">
              Plan gratis: 3 presupuestos al mes. Sin tarjeta de crédito.
            </p>
          )}
        </form>
      </div>
    </div>
  )
}
