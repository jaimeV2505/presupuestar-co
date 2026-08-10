import React, { useState, useEffect } from 'react'
import { Building2, Database, BookOpen, DollarSign, Brain, TrendingUp } from 'lucide-react'
import { feedbackAPI } from '../../services/api'

export default function Header({ onShowPrecios, onShowTablas, dbStats }) {
  const [fbStats, setFbStats] = useState(null)

  useEffect(() => {
    feedbackAPI.stats().then(r => setFbStats(r.data)).catch(()=>{})
  }, [])

  return (
    <header className="hero-gradient text-white shadow-xl">
      <div className="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/20">
            <Building2 size={22}/>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg leading-tight tracking-tight">PresupuestarCO</h1>
              <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-full font-semibold tracking-wide">v7.0</span>
            </div>
            <p className="text-blue-200 text-[11px] mt-0.5">
              APU 2026 · OCR · Predim · Flete · Desglose · NSR-10
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Stats de la BD */}
          {dbStats && (
            <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 bg-white/10 rounded-xl text-xs font-medium border border-white/15">
              <Database size={13} className="text-blue-200"/>
              <span className="text-blue-100">{dbStats.total_actividades?.toLocaleString('es-CO')} APUs</span>
            </div>
          )}

          {/* Indicador de aprendizaje */}
          {fbStats && (fbStats.total_correcciones > 0 || fbStats.patrones_aprendidos > 0) && (
            <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 rounded-xl text-xs font-medium border border-emerald-400/30">
              <Brain size={13} className="text-emerald-300"/>
              <span className="text-emerald-200">
                {fbStats.patrones_aprendidos} patrón{fbStats.patrones_aprendidos!==1?'es':''} aprendido{fbStats.patrones_aprendidos!==1?'s':''}
              </span>
            </div>
          )}

          <button onClick={onShowPrecios}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium border border-white/15 transition-all">
            <DollarSign size={14}/>Precios
          </button>
          <button onClick={onShowTablas}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium border border-white/15 transition-all">
            <TrendingUp size={14}/>Tablas
          </button>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
            className="hidden sm:flex items-center gap-1.5 px-3.5 py-1.5 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium border border-white/15 transition-all">
            <BookOpen size={14}/>API
          </a>
        </div>
      </div>

      {/* Sub-banner de capacidades */}
      <div className="border-t border-white/10">
        <div className="max-w-5xl mx-auto px-4 py-2 flex items-center gap-6 text-[11px] text-blue-200">
          <span className="flex items-center gap-1.5"><span>🏛</span> Concreto reforzado</span>
          <span className="flex items-center gap-1.5"><span>⚙️</span> Estructura metálica</span>
          <span className="flex items-center gap-1.5"><span>🕳</span> Caissones y pilotes</span>
          <span className="flex items-center gap-1.5"><span>🗻</span> Muros de contención</span>
          <span className="hidden md:flex items-center gap-1.5">
            <Brain size={11} className="text-emerald-300"/>
            <span className="text-emerald-300">
              {fbStats ? `${fbStats.total_planos} plano${fbStats.total_planos!==1?'s':''} analizados` : 'Aprendizaje activo'}
            </span>
          </span>
        </div>
      </div>
    </header>
  )
}
