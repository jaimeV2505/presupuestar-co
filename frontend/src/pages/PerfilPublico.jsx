import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Building2, MapPin, MessageCircle, CheckCircle2 } from 'lucide-react'
import { shareAPI } from '../services/api'

const Estrellas = ({ n }) => (
  <span className="text-amber-400">{'★'.repeat(Math.round(n))}<span className="text-slate-200">{'★'.repeat(5 - Math.round(n))}</span></span>
)

export default function PerfilPublico() {
  const { slug } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    shareAPI.perfilPublico(slug).then(setData).catch(() => setError(true))
  }, [slug])

  if (error) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400 text-sm">
      Perfil no encontrado
    </div>
  )
  if (!data) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400 text-sm">
      Cargando perfil...
    </div>
  )

  const s = data.stats
  const wa = (data.telefono || '').replace(/\D/g, '')

  return (
    <div className="min-h-screen bg-slate-100 pb-16">
      {/* Header */}
      <div className="bg-gradient-to-br from-navy-900 to-navy-600 text-white px-4 pt-10 pb-14 text-center">
        {data.logo_b64 ? (
          <img src={data.logo_b64} alt="" className="w-20 h-20 rounded-2xl object-contain bg-white p-1.5 mx-auto shadow-lg" />
        ) : (
          <div className="w-20 h-20 bg-white/10 rounded-2xl flex items-center justify-center mx-auto">
            <Building2 className="w-9 h-9" />
          </div>
        )}
        <h1 className="text-xl font-black mt-3">{data.empresa || data.nombre}</h1>
        {data.empresa && <p className="text-sm text-blue-200">{data.nombre}</p>}
        <p className="text-xs text-blue-300 mt-1 flex items-center justify-center gap-1">
          <MapPin className="w-3 h-3" /> {data.ciudad?.charAt(0).toUpperCase() + data.ciudad?.slice(1)}, Colombia
        </p>
      </div>

      {/* Stats */}
      <div className="max-w-lg mx-auto px-4 -mt-8">
        <div className="bg-white rounded-2xl shadow-lg p-4 grid grid-cols-3 divide-x divide-slate-100 text-center">
          <div>
            <p className="text-2xl font-black text-amber-500">{s.promedio > 0 ? s.promedio : '—'}</p>
            <p className="text-[10px] text-slate-400">Calificación<br/>({s.total} reseña{s.total !== 1 ? 's' : ''})</p>
          </div>
          <div>
            <p className="text-2xl font-black text-navy-600">{s.obras_terminadas}</p>
            <p className="text-[10px] text-slate-400">Obras<br/>terminadas</p>
          </div>
          <div>
            <p className="text-2xl font-black text-emerald-500">{s.pct_recomienda}%</p>
            <p className="text-[10px] text-slate-400">Lo<br/>recomiendan</p>
          </div>
        </div>

        {/* Resenas */}
        <div className="mt-5">
          <h2 className="text-sm font-bold text-slate-700 mb-2 px-1">Lo que dicen sus clientes</h2>
          {data.resenas.length === 0 ? (
            <p className="text-center text-xs text-slate-400 py-8 bg-white rounded-2xl">
              Aún no hay reseñas publicadas
            </p>
          ) : (
            <div className="space-y-2.5">
              {data.resenas.map((r, i) => (
                <div key={i} className="bg-white rounded-2xl p-4">
                  <div className="flex items-center justify-between">
                    <Estrellas n={r.estrellas} />
                    <span className="text-[10px] text-slate-300">{r.fecha}</span>
                  </div>
                  <p className="text-sm text-slate-600 mt-2 leading-relaxed">"{r.comentario}"</p>
                  <div className="flex items-center justify-between mt-2">
                    <p className="text-[10px] text-slate-400">📋 {r.proyecto}</p>
                    {r.recomendaria && (
                      <span className="text-[9px] text-emerald-600 flex items-center gap-0.5">
                        <CheckCircle2 className="w-3 h-3" /> Lo recomienda
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Contactar */}
        {wa && (
          <a href={`https://wa.me/${wa.startsWith('57') ? wa : '57' + wa}?text=${encodeURIComponent('Hola! Vi tu perfil en PresupuestarCO y quiero cotizar una obra')}`}
             target="_blank" rel="noreferrer"
             className="mt-5 flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-sm rounded-2xl py-3.5 transition">
            <MessageCircle className="w-4 h-4" /> Cotizar con {data.empresa || data.nombre.split(' ')[0]}
          </a>
        )}

        <p className="text-center text-[10px] text-slate-400 mt-6">
          Perfil verificado por <Link to="/" className="font-semibold text-navy-500">PresupuestarCO</Link> —
          las calificaciones provienen de obras reales terminadas en la plataforma
        </p>
      </div>
    </div>
  )
}
