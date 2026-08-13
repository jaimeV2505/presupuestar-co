import { useEffect, useState } from 'react'

/**
 * Lightbox — galeria a pantalla completa para las fotos de la obra.
 * Modular: recibe fotos[] y el indice inicial; flechas, swipe basico y contador.
 */
export default function Lightbox({ fotos, inicial = 0, onCerrar }) {
  const [i, setI] = useState(inicial)
  useEffect(() => {
    const tecla = (e) => {
      if (e.key === 'Escape') onCerrar()
      if (e.key === 'ArrowRight') setI(x => (x + 1) % fotos.length)
      if (e.key === 'ArrowLeft') setI(x => (x - 1 + fotos.length) % fotos.length)
    }
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [fotos.length, onCerrar])

  let toqueX = null
  return (
    <div className="fixed inset-0 z-[70] bg-black/95 flex items-center justify-center"
         onClick={onCerrar}
         onTouchStart={e => { toqueX = e.touches[0].clientX }}
         onTouchEnd={e => {
           if (toqueX == null) return
           const dx = e.changedTouches[0].clientX - toqueX
           if (dx < -40) setI(x => (x + 1) % fotos.length)
           if (dx > 40) setI(x => (x - 1 + fotos.length) % fotos.length)
           toqueX = null
         }}>
      <button className="absolute top-4 right-4 text-white/70 text-2xl font-bold z-10"
              onClick={onCerrar} aria-label="Cerrar">✕</button>
      {fotos.length > 1 && (
        <>
          <button className="absolute left-2 text-white/60 text-3xl px-3 py-6 z-10"
                  onClick={e => { e.stopPropagation(); setI(x => (x - 1 + fotos.length) % fotos.length) }}>‹</button>
          <button className="absolute right-2 text-white/60 text-3xl px-3 py-6 z-10"
                  onClick={e => { e.stopPropagation(); setI(x => (x + 1) % fotos.length) }}>›</button>
        </>
      )}
      <img src={fotos[i]} alt="" className="max-h-[88vh] max-w-[94vw] object-contain rounded-lg"
           onClick={e => e.stopPropagation()} />
      {fotos.length > 1 && (
        <p className="absolute bottom-4 text-white/60 text-xs">{i + 1} / {fotos.length}</p>
      )}
    </div>
  )
}
