import React, { useEffect, useState, useRef } from 'react'

// ═══════════════════════════════════════════════════════════════════════════
// DIALOGO DE LA PLATAFORMA — adios a los prompt/confirm/alert del navegador.
// Uso (promesas, desde cualquier parte):
//   const nombre = await pedirTexto({ titulo, mensaje?, placeholder?, valorInicial?, confirmar? })
//     -> string | null (cancelo)
//   const ok = await confirmarDialogo({ titulo, mensaje?, confirmar?, peligro? })
//     -> true | false
// <DialogoHost/> se monta UNA vez en main.jsx. Nace de la auditoria de
// dialogos nativos (18/8/2026): la plataforma habla con su propia voz.
// ═══════════════════════════════════════════════════════════════════════════

let _abrir = null

export function pedirTexto(opts) {
  return new Promise(res => {
    if (!_abrir) { res(window.prompt(opts.titulo, opts.valorInicial || '')) ; return }
    _abrir({ tipo: 'texto', ...opts, res })
  })
}

export function confirmarDialogo(opts) {
  return new Promise(res => {
    if (!_abrir) { res(window.confirm(opts.titulo)); return }
    _abrir({ tipo: 'confirmar', ...opts, res })
  })
}

export default function DialogoHost() {
  const [d, setD] = useState(null)
  const [valor, setValor] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    _abrir = (cfg) => { setD(cfg); setValor(cfg.valorInicial || '') }
    return () => { _abrir = null }
  }, [])

  useEffect(() => {
    if (d?.tipo === 'texto') setTimeout(() => inputRef.current?.focus(), 50)
    const onKey = (e) => {
      if (!d) return
      if (e.key === 'Escape') cerrar(d.tipo === 'texto' ? null : false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [d])

  if (!d) return null

  const cerrar = (resultado) => { d.res(resultado); setD(null) }
  const aceptar = () => cerrar(d.tipo === 'texto' ? valor : true)

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-[2px] z-[100] flex items-center justify-center p-4"
         onClick={() => cerrar(d.tipo === 'texto' ? null : false)}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-5" onClick={e => e.stopPropagation()}>
        <h3 className="font-black text-slate-800 text-base">{d.titulo}</h3>
        {d.mensaje && (
          <p className="text-xs text-slate-500 mt-2 whitespace-pre-line leading-relaxed">{d.mensaje}</p>
        )}
        {d.tipo === 'texto' && (
          <input ref={inputRef} value={valor} onChange={e => setValor(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter') aceptar() }}
                 placeholder={d.placeholder || ''}
                 className="mt-3 w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-navy-400" />
        )}
        <div className="flex gap-2 mt-4">
          <button onClick={() => cerrar(d.tipo === 'texto' ? null : false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-200 text-sm font-bold text-slate-500 hover:bg-slate-50">
            Cancelar
          </button>
          <button onClick={aceptar}
                  className={`flex-1 py-2.5 rounded-xl text-sm font-bold text-white ${d.peligro ? 'bg-red-500 hover:bg-red-600' : 'bg-navy-600 hover:bg-navy-700'}`}>
            {d.confirmar || (d.tipo === 'texto' ? 'Aceptar' : 'Sí, continuar')}
          </button>
        </div>
      </div>
    </div>
  )
}
