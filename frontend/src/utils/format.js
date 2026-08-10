export const COP = v => new Intl.NumberFormat('es-CO',{style:'currency',currency:'COP',minimumFractionDigits:0,maximumFractionDigits:0}).format(v||0)
export const NUM = (v,d=2) => new Intl.NumberFormat('es-CO',{minimumFractionDigits:0,maximumFractionDigits:d}).format(v||0)
export const MILL = v => {
  if(v>=1e9) return `$${(v/1e9).toFixed(2)}B`
  if(v>=1e6) return `$${(v/1e6).toFixed(1)}M`
  if(v>=1e3) return `$${(v/1e3).toFixed(0)}K`
  return COP(v)
}
export const TIPO_COLORS = {
  columnas:    {bg:'bg-blue-50',   text:'text-blue-700',   border:'border-blue-200'},
  vigas:       {bg:'bg-emerald-50',text:'text-emerald-700',border:'border-emerald-200'},
  losa:        {bg:'bg-amber-50',  text:'text-amber-700',  border:'border-amber-200'},
  cimentacion: {bg:'bg-red-50',    text:'text-red-700',    border:'border-red-200'},
  muros:       {bg:'bg-purple-50', text:'text-purple-700', border:'border-purple-200'},
  escaleras:   {bg:'bg-cyan-50',   text:'text-cyan-700',   border:'border-cyan-200'},
  cubierta:    {bg:'bg-orange-50', text:'text-orange-700', border:'border-orange-200'},
  viga_amarre: {bg:'bg-indigo-50', text:'text-indigo-700', border:'border-indigo-200'},
  otros:       {bg:'bg-slate-50',  text:'text-slate-600',  border:'border-slate-200'},
}
export const CAP_COLORS = {
  'CIMENTACIONES':'bg-red-500','ESTRUCTURAS EN CONCRETO':'bg-blue-600',
  'MAMPOSTERÍA':'bg-purple-500','PAÑETES (REVOQUES)':'bg-violet-400',
  'CUBIERTAS':'bg-orange-500','INSTALACIONES ELÉCTRICAS':'bg-yellow-500',
  'INSTALACIONES HIDRÁULICAS':'bg-cyan-500','INSTALACIONES SANITARIAS':'bg-teal-500',
  'MOVIMIENTO DE TIERRAS':'bg-stone-500','OTROS':'bg-slate-400',
}
