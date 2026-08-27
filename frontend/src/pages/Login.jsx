import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Building2 } from 'lucide-react'
import { authAPI, recuperarAPI } from '../services/api'

export default function Login({ modo = 'login' }) {
  const nav = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', nombre: '', empresa: '', telefono: '' , acepta_terminos: false })
  const [loading, setLoading] = useState(false)
  const esRegistro = modo === 'registro'
  const [olvide, setOlvide] = useState(false)
  const [enviado, setEnviado] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (olvide) {
      if (!form.email) { toast.error('Escribe tu correo'); return }
      setLoading(true)
      try {
        await recuperarAPI.olvide(form.email)
        setEnviado(true)
      } catch { setEnviado(true) }
      finally { setLoading(false) }
      return
    }
    if (!form.email || !form.password) { toast.error('Email y contraseña requeridos'); return }
    if (esRegistro && !form.nombre) { toast.error('Tu nombre es requerido'); return }
    if (esRegistro && !form.acepta_terminos) { toast.error('Debes aceptar los términos y la política de datos'); return }
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

          <input data-testid="auth-email" className="input" type="email" placeholder="Email *" value={form.email} onChange={set('email')} autoComplete="email" />
          {!olvide && <input data-testid="auth-password" className="input" type="password" placeholder={esRegistro ? 'Contraseña (mínimo 8 caracteres) *' : 'Contraseña *'}
                 value={form.password} onChange={set('password')} autoComplete={esRegistro ? 'new-password' : 'current-password'} />}

          {esRegistro && (
            <label className="flex items-start gap-2 text-[11px] text-slate-500 cursor-pointer">
              <input type="checkbox" data-testid="check-terminos" className="mt-0.5" checked={!!form.acepta_terminos}
                     onChange={e => setForm(f => ({ ...f, acepta_terminos: e.target.checked }))} />
              <span>Acepto los <a href="/legal" target="_blank" rel="noreferrer" className="underline text-navy-600">términos y la política de tratamiento de datos</a> (Ley 1581 de 2012)</span>
            </label>
          )}
          <button data-testid="auth-submit" disabled={loading}
                  className="w-full bg-navy-600 hover:bg-navy-700 text-white font-semibold rounded-xl py-3 transition disabled:opacity-50">
            {loading ? 'Un momento...' : olvide ? 'Enviarme el enlace' : esRegistro ? 'Crear cuenta gratis' : 'Entrar'}
          </button>

          {olvide && enviado && (
            <p className="text-center text-xs text-emerald-600 bg-emerald-50 rounded-xl p-3">
              ✓ Si el correo existe, te enviamos el enlace (revisa spam). Vale por 30 minutos.
            </p>
          )}
          {!esRegistro && (
            <p className="text-center text-xs">
              <button type="button"
                      onClick={() => { setOlvide(v => !v); setEnviado(false) }}
                      className="text-slate-400 hover:text-navy-600 underline">
                {olvide ? '← Volver a iniciar sesión' : '¿Olvidaste tu contraseña?'}
              </button>
            </p>
          )}
          {esRegistro && (
            <p className="text-center text-[10px] text-slate-400">
              Al crear tu cuenta aceptas los{' '}
              <Link to="/legal" className="underline text-slate-500">Términos y la Política de datos</Link>
              {' '}(Ley 1581 de 2012)
            </p>
          )}

          <p className="text-center text-sm text-slate-500">
            {esRegistro ? (
              <>¿Ya tienes cuenta? <Link to="/login" className="text-navy-600 font-medium">Inicia sesión</Link></>
            ) : (
              <>¿Primera vez? <Link to="/registro" className="text-navy-600 font-medium">Crea tu cuenta gratis</Link></>
            )}
          </p>
          {esRegistro && (
            <p className="text-xs text-slate-400 text-center">
              Gratis durante la fase de lanzamiento. Sin tarjeta de crédito.
            </p>
          )}
        </form>
      </div>
    </div>
  )
}
