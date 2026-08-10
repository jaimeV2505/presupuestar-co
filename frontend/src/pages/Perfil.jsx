import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Upload, Building2, Save } from 'lucide-react'
import { authAPI } from '../services/api'

const CONDICIONES_EJEMPLO = `Validez de la oferta: 15 dias calendario.
Forma de pago: 50% anticipo, 30% avance de obra, 20% contra entrega.
No incluye: tramites ante curaduria, disenos estructurales ni licencias.
Los precios de materiales estan sujetos a variacion del mercado.
Cualquier trabajo adicional se cotizara por separado.`

export default function Perfil() {
  const nav = useNavigate()
  const [form, setForm] = useState({ nombre: '', empresa: '', telefono: '', ciudad: 'bogota', condiciones: '' })
  const [logo, setLogo] = useState('')
  const [guardando, setGuardando] = useState(false)
  const fileRef = useRef(null)

  useEffect(() => {
    authAPI.yo().then(u => {
      setForm({
        nombre: u.nombre || '', empresa: u.empresa || '',
        telefono: u.telefono || '', ciudad: u.ciudad || 'bogota',
        condiciones: u.condiciones || '',
      })
      setLogo(u.logo_b64 || '')
    }).catch(e => toast.error(e.message))
  }, [])

  const subirLogo = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 500 * 1024) { toast.error('El logo debe pesar menos de 500KB'); return }
    const reader = new FileReader()
    reader.onload = () => setLogo(reader.result)
    reader.readAsDataURL(file)
  }

  const guardar = async () => {
    if (!form.nombre.trim()) { toast.error('Tu nombre es requerido'); return }
    setGuardando(true)
    try {
      const u = await authAPI.actualizarPerfil({ ...form, logo_b64: logo })
      localStorage.setItem('usuario', JSON.stringify(u))
      toast.success('Perfil guardado')
    } catch (e) { toast.error(e.message) }
    finally { setGuardando(false) }
  }

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => nav('/')} className="p-2 hover:bg-slate-100 rounded-lg">
              <ArrowLeft className="w-4 h-4 text-slate-600" />
            </button>
            <h1 className="font-semibold text-slate-800">Perfil de empresa</h1>
          </div>
          <button onClick={guardar} disabled={guardando}
                  className="flex items-center gap-2 bg-navy-600 hover:bg-navy-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition disabled:opacity-50">
            <Save className="w-4 h-4" /> {guardando ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        {/* Logo */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Logo</h3>
          <p className="text-xs text-slate-400 mb-3">Aparece en tus PDFs y en el enlace que ve tu cliente.</p>
          <div className="flex items-center gap-4">
            {logo ? (
              <img src={logo} alt="Logo" className="w-20 h-20 rounded-xl object-contain border border-slate-200 bg-white p-1" />
            ) : (
              <div className="w-20 h-20 rounded-xl border-2 border-dashed border-slate-300 flex items-center justify-center">
                <Building2 className="w-8 h-8 text-slate-300" />
              </div>
            )}
            <div>
              <button onClick={() => fileRef.current?.click()}
                      className="flex items-center gap-2 text-sm font-medium text-navy-600 border border-navy-200 rounded-xl px-4 py-2 hover:bg-navy-50 transition">
                <Upload className="w-4 h-4" /> Subir logo
              </button>
              <p className="text-[11px] text-slate-400 mt-1.5">PNG o JPG, máximo 500KB</p>
              {logo && (
                <button onClick={() => setLogo('')} className="text-[11px] text-red-400 mt-1">Quitar logo</button>
              )}
            </div>
            <input ref={fileRef} type="file" accept="image/png,image/jpeg" className="hidden" onChange={subirLogo} />
          </div>
        </div>

        {/* Datos */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
          <h3 className="text-sm font-semibold text-slate-700">Datos de contacto</h3>
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Tu nombre *</label>
            <input className="input" value={form.nombre} onChange={set('nombre')} />
          </div>
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Empresa</label>
            <input className="input" placeholder="Construcciones López SAS" value={form.empresa} onChange={set('empresa')} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">WhatsApp</label>
              <input className="input" placeholder="300 123 4567" value={form.telefono} onChange={set('telefono')} />
            </div>
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Ciudad (precios base)</label>
              <select className="input" value={form.ciudad} onChange={set('ciudad')}>
                <option value="bogota">Bogotá D.C.</option>
                <option value="medellin">Medellín</option>
                <option value="cali">Cali</option>
                <option value="barranquilla">Barranquilla</option>
                <option value="bucaramanga">Bucaramanga</option>
                <option value="cartagena">Cartagena</option>
                <option value="pereira">Pereira</option>
                <option value="manizales">Manizales</option>
                <option value="ibague">Ibagué</option>
                <option value="cucuta">Cúcuta</option>
                <option value="villavicencio">Villavicencio</option>
                <option value="monteria">Montería</option>
                <option value="pasto">Pasto</option>
              </select>
            </div>
          </div>
        </div>

        {/* Condiciones estandar */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-semibold text-slate-700">Condiciones estándar</h3>
            <button onClick={() => setForm(f => ({ ...f, condiciones: CONDICIONES_EJEMPLO }))}
                    className="text-[11px] text-navy-600 font-medium">
              Usar ejemplo
            </button>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Se incluyen automáticamente en cada PDF y en el enlace del cliente:
            validez de la oferta, forma de pago, qué no incluye...
          </p>
          <textarea className="input min-h-[140px] text-xs leading-relaxed" placeholder={CONDICIONES_EJEMPLO}
                    value={form.condiciones} onChange={set('condiciones')} maxLength={3000} />
          <p className="text-[10px] text-slate-300 text-right mt-1">{form.condiciones.length}/3000</p>
        </div>
      </main>
    </div>
  )
}
