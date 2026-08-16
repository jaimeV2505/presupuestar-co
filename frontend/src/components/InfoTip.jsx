import { useState } from 'react'

/**
 * InfoTip — el traductor de jerga para el cliente.
 * Un (i) discreto que al tocarlo explica el termino en lenguaje humano.
 * Modular: se usa en cualquier pagina; cierra al tocar afuera.
 */
export default function InfoTip({ texto }) {
  const [abierto, setAbierto] = useState(false)
  return (
    <span className="relative inline-block align-middle">
      <button onClick={e => { e.stopPropagation(); setAbierto(v => !v) }}
              className="w-4 h-4 inline-flex items-center justify-center rounded-full bg-slate-200 text-slate-500 text-[9px] font-bold ml-1 hover:bg-slate-300"
              aria-label="Que significa esto">
        i
      </button>
      {abierto && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setAbierto(false)} />
          <span className="absolute z-50 left-1/2 -translate-x-1/2 bottom-6 w-56 bg-slate-800 text-white text-[11px] leading-relaxed rounded-xl p-3 shadow-xl normal-case font-normal tracking-normal text-left">
            {texto}
            <span className="absolute left-1/2 -translate-x-1/2 -bottom-1 w-2 h-2 bg-slate-800 rotate-45" />
          </span>
        </>
      )}
    </span>
  )
}
