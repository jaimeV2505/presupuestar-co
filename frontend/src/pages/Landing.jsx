import React from 'react'
import { Link } from 'react-router-dom'
import { Building2, Search, MessageCircle, FileSignature, HardHat, Calculator,
         CheckCircle2, Zap, Shield, ChevronRight, Eye, Star, Camera,
         FileSpreadsheet, MapPin, Hash, ClipboardCheck } from 'lucide-react'

const CHECK = ({ children, bold }) => (
  <li className="flex items-start gap-2.5 text-sm text-slate-600">
    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
    <span className={bold ? 'font-bold text-slate-800' : ''}>{children}</span>
  </li>
)

const FUNCIONES = [
  [Search, 'Base APU 2026', '2.288 actividades de construcción con precios de referencia, organizadas por capítulos: preliminares, cimentación, estructura, mampostería, acabados...'],
  [MapPin, 'Precios por ciudad', 'Factores regionales para 13 ciudades colombianas. Bogotá no cuesta lo mismo que Montería — tu presupuesto lo sabe.'],
  [Calculator, 'Calculadora de cantidades', '¿3 columnas de 30×30 por 3 metros? Escribes las dimensiones y la app convierte a m³ sola. Volumen, área y metro lineal.'],
  [Shield, 'AIU + IVA como manda la ley', 'A, I y U configurables por separado. IVA 19% solo sobre la utilidad (Art. 462-1 ET). Deja de regalar plata por calcular mal.'],
  [Hash, 'Numeración automática', 'COT-2026-0001, 0002... Cada cotización con su número, fecha y estado. Tu historial ordenado y buscable.'],
  [Eye, 'Seguimiento de estados', 'Borrador → Enviado → 👁 Visto → ✓ Aceptado → 🏁 Terminado. Sabes exactamente en qué va cada negocio.'],
  [MessageCircle, 'Enlace WhatsApp con "visto"', 'Tu cliente abre el presupuesto en su celular sin instalar nada. Tú ves cuándo lo abrió y cuántas veces.'],
  [FileSignature, 'Contrato con firma digital', 'Al aceptar, el cliente firma un Contrato de Ejecución de Obra Civil de 8 cláusulas generado automático. PDF para ambos.'],
  [HardHat, 'Avances de obra con $$', 'Marcas el % por actividad y el sistema calcula el valor ejecutado ponderado. El cliente lo ve en tiempo real.'],
  [Camera, 'Fotos de avance', 'Hasta 3 fotos por corte de obra. El cliente sigue su proyecto desde el mismo enlace del presupuesto.'],
  [Star, 'Encuesta al terminar', 'Al culminar la obra, el cliente califica tu trabajo (1-5 ⭐). Construyes reputación con cada proyecto.'],
  [FileSpreadsheet, 'PDF y Excel con tu logo', 'Exporta con tu marca, tus datos y tus condiciones estándar incluidas automáticamente.'],
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── NAV ── */}
      <nav className="sticky top-0 z-50 bg-navy-800/95 backdrop-blur border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white">PresupuestarCO</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="#funciones" className="hidden sm:block text-sm text-blue-200 hover:text-white transition">Funciones</a>
            <a href="#precios" className="hidden sm:block text-sm text-blue-200 hover:text-white transition">Precios</a>
            <Link to="/login" className="text-sm text-blue-100 font-medium px-3 py-1.5">Entrar</Link>
            <Link to="/registro" className="text-sm bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-4 py-2 rounded-xl transition">
              Empezar gratis
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <header className="bg-gradient-to-br from-navy-900 via-navy-800 to-navy-600 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10" style={{backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px)', backgroundSize: '32px 32px'}}></div>
        <div className="max-w-6xl mx-auto px-4 pt-16 pb-20 relative">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold bg-emerald-500/20 text-emerald-300 px-3 py-1.5 rounded-full mb-5">
              <Zap className="w-3.5 h-3.5" /> Todas las funciones gratis — paga solo si cotizas en volumen
            </span>
            <h1 className="text-4xl sm:text-5xl font-black leading-tight tracking-tight">
              Presupuestos de obra profesionales <span className="text-emerald-400">en minutos</span>, no en madrugadas
            </h1>
            <p className="text-lg text-blue-200 mt-5 leading-relaxed">
              Cotiza con la base APU 2026, comparte por WhatsApp, tu cliente firma el
              contrato digital y sigue los avances de su obra. Todo en una sola herramienta
              hecha para el contratista colombiano.
            </p>
            <div className="flex flex-wrap gap-3 mt-8">
              <Link to="/registro" className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-6 py-3.5 rounded-xl transition text-sm">
                Crear cuenta gratis <ChevronRight className="w-4 h-4" />
              </Link>
              <a href="#funciones" className="flex items-center gap-2 border border-white/20 hover:bg-white/5 text-white font-medium px-6 py-3.5 rounded-xl transition text-sm">
                Ver todas las funciones
              </a>
            </div>
            <p className="text-xs text-blue-300 mt-4">Sin tarjeta de crédito · 3 presupuestos gratis al mes · Listo en 2 minutos</p>
          </div>

          <div className="hidden lg:block absolute right-4 top-16 w-80 bg-white rounded-2xl shadow-2xl p-4 rotate-2">
            <div className="flex justify-between items-center mb-3">
              <div>
                <p className="text-[10px] font-bold text-navy-500">COT-2026-0037</p>
                <p className="text-xs font-semibold text-slate-700">Remodelación Casa López</p>
              </div>
              <span className="text-[9px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">✓ Firmado</span>
            </div>
            {[['Excavación zapatas 2×2×1.2', '$2.100.000'], ['Columnas 4000 PSI ×15', '$49.500.000'], ['Placa aligerada 360 m²', '$129.600.000']].map(([d, v], i) => (
              <div key={i} className="flex justify-between py-1.5 border-b border-slate-50 text-[10px]">
                <span className="text-slate-500">{d}</span>
                <span className="text-slate-700 font-medium">{v}</span>
              </div>
            ))}
            <div className="flex justify-between mt-3 bg-navy-800 text-white rounded-lg px-3 py-2">
              <span className="text-[10px] uppercase text-blue-200">Total</span>
              <span className="text-sm font-black">$276.675.000</span>
            </div>
            <div className="flex items-center gap-1.5 mt-2.5 text-[9px] text-slate-400">
              <MessageCircle className="w-3 h-3 text-emerald-500" /> Visto por el cliente · hace 5 min
            </div>
          </div>
        </div>
      </header>

      {/* ── CIFRAS ── */}
      <section className="bg-navy-800 border-t border-white/5 py-6">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          {[['2.288', 'actividades APU 2026'], ['13', 'ciudades con precios'], ['8', 'cláusulas de contrato'], ['100%', 'hecho en Colombia 🇨🇴']].map(([n, l], i) => (
            <div key={i}>
              <p className="text-2xl font-black text-emerald-400">{n}</p>
              <p className="text-[11px] text-blue-300 mt-0.5">{l}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── PROBLEMA ── */}
      <section className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl sm:text-3xl font-black text-slate-800">¿Te suena familiar?</h2>
        <div className="grid sm:grid-cols-3 gap-4 mt-8">
          {[
            ['😩', 'Excel hasta medianoche', 'Buscando precios viejos, cuadrando fórmulas que se dañan'],
            ['👻', 'Clientes que desaparecen', 'Envías el PDF por WhatsApp y nunca sabes si lo abrieron'],
            ['🤝', 'Acuerdos de palabra', '"Arrancamos y después firmamos" — y después nadie firma'],
          ].map(([e, t, d], i) => (
            <div key={i} className="bg-slate-50 rounded-2xl p-5">
              <span className="text-3xl">{e}</span>
              <p className="font-bold text-slate-700 mt-2 text-sm">{t}</p>
              <p className="text-xs text-slate-500 mt-1">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── SHOWCASE: 3 funciones estrella ── */}
      <section className="bg-slate-50 py-16">
        <div className="max-w-5xl mx-auto px-4 space-y-14">

          {/* WhatsApp + visto */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <span className="text-[11px] font-black uppercase tracking-wider text-emerald-600">Cierra más negocios</span>
              <h3 className="text-2xl font-black text-slate-800 mt-1.5">Tu presupuesto vive en WhatsApp, como tus clientes</h3>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">
                Nada de PDFs pesados que nadie abre. Compartes un enlace profesional con tu logo;
                tu cliente lo ve en su celular al instante y tú recibes el <strong>"visto"</strong> —
                para llamarlo en el momento exacto en que está pensando en tu oferta.
              </p>
              <ul className="space-y-2 mt-4">
                <CHECK>Notificación de cuándo y cuántas veces lo abrió</CHECK>
                <CHECK>Botones de aceptar o rechazar — respuestas claras, no silencio</CHECK>
                <CHECK>El cliente no instala nada ni crea cuenta</CHECK>
              </ul>
            </div>
            <div className="bg-white rounded-2xl shadow-lg p-5 border border-slate-100">
              <div className="bg-navy-800 rounded-xl p-4 text-white">
                <p className="text-[9px] text-blue-300 uppercase">Presupuesto de obra · COT-2026-0012</p>
                <p className="text-sm font-bold mt-0.5">Cubierta metálica Local 3</p>
                <p className="text-2xl font-black mt-2">$18.450.000</p>
              </div>
              <div className="flex gap-2 mt-3">
                <div className="flex-1 text-center text-[10px] py-2.5 rounded-lg border border-slate-200 text-slate-500">Preguntar</div>
                <div className="flex-[2] text-center text-[10px] py-2.5 rounded-lg bg-emerald-500 text-white font-bold">✓ Aceptar presupuesto</div>
              </div>
              <div className="flex items-center gap-1.5 mt-3 text-[10px] text-violet-600 bg-violet-50 rounded-lg px-2.5 py-1.5 w-fit">
                <Eye className="w-3 h-3" /> Visto 3 veces · última hace 5 min
              </div>
            </div>
          </div>

          {/* Contrato */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="order-2 md:order-1 bg-white rounded-2xl shadow-lg p-5 border border-slate-100">
              <p className="text-[10px] font-black text-center text-slate-700">CONTRATO DE EJECUCIÓN DE OBRA CIVIL</p>
              <div className="mt-3 space-y-2">
                {['PRIMERA: OBJETO', 'SEGUNDA: TÉRMINO — 45 días hábiles', 'TERCERA: COSTO — $18.450.000', 'CUARTA: ANTICIPO 50% · SALDO 50%'].map((c, i) => (
                  <div key={i} className="text-[9px] text-slate-500 bg-slate-50 rounded-lg px-2.5 py-1.5">{c}</div>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-100">
                <div className="text-center">
                  <p className="text-[9px] font-bold text-slate-600">CONTRATANTE</p>
                  <p className="text-[9px] text-emerald-600 mt-0.5">✓ Firmado · 10/08 14:32</p>
                </div>
                <div className="text-center">
                  <p className="text-[9px] font-bold text-slate-600">CONTRATISTA</p>
                  <p className="text-[9px] text-emerald-600 mt-0.5">✓ Emitido digitalmente</p>
                </div>
              </div>
            </div>
            <div className="order-1 md:order-2">
              <span className="text-[11px] font-black uppercase tracking-wider text-navy-500">Trabaja con respaldo</span>
              <h3 className="text-2xl font-black text-slate-800 mt-1.5">Se acabaron los acuerdos de palabra</h3>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">
                Cuando tu cliente acepta, no solo dice "sí": <strong>firma un Contrato de
                Ejecución de Obra Civil</strong> generado automáticamente con tus condiciones —
                plazo, anticipo, forma de pago, responsabilidades. Con nombre, cédula, fecha y hora registrados.
              </p>
              <ul className="space-y-2 mt-4">
                <CHECK>8 cláusulas generadas desde tu presupuesto</CHECK>
                <CHECK>Evidencia digital amparada en la Ley 527 de 1999</CHECK>
                <CHECK>PDF del contrato firmado para ambas partes</CHECK>
                <CHECK>El presupuesto se bloquea tras la firma — nadie cambia las reglas</CHECK>
              </ul>
            </div>
          </div>

          {/* Avances */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <span className="text-[11px] font-black uppercase tracking-wider text-amber-600">Cobra sin peleas</span>
              <h3 className="text-2xl font-black text-slate-800 mt-1.5">Avances de obra en plata, no en cuentos</h3>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">
                Marcas el % de avance <strong>por cada actividad del presupuesto</strong> y el sistema
                calcula el valor ejecutado ponderado. Tu cliente lo ve en tiempo real con fotos —
                cuando pidas el siguiente pago, los números ya están sobre la mesa.
              </p>
              <ul className="space-y-2 mt-4">
                <CHECK>Avance ponderado por el valor de cada actividad</CHECK>
                <CHECK>"$12.4M ejecutados de $36.4M" — claridad total</CHECK>
                <CHECK>Fotos por corte de obra</CHECK>
                <CHECK>Al terminar: encuesta de satisfacción y tu calificación ⭐</CHECK>
              </ul>
            </div>
            <div className="bg-white rounded-2xl shadow-lg p-5 border border-slate-100">
              <div className="flex justify-between items-center">
                <p className="text-xs font-bold text-slate-700">Avance de tu obra</p>
                <span className="text-sm font-black text-emerald-600">64%</span>
              </div>
              <div className="h-2.5 bg-slate-100 rounded-full mt-2 overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{width: '64%'}}></div>
              </div>
              <div className="flex justify-between text-[10px] bg-emerald-50 rounded-lg p-2.5 mt-3">
                <span className="text-emerald-700">Valor ejecutado</span>
                <span className="font-bold text-emerald-700">$11.8M de $18.4M</span>
              </div>
              <div className="mt-3 space-y-1.5">
                {[['Excavación y zapatas', 100], ['Columnas y pedestales', 80], ['Placa aligerada', 35]].map(([a, p], i) => (
                  <div key={i} className="flex items-center gap-2 text-[9px]">
                    <span className="flex-1 text-slate-500">{a}</span>
                    <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-400 rounded-full" style={{width: `${p}%`}}></div>
                    </div>
                    <span className="text-slate-400 w-7 text-right">{p}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── TODAS LAS FUNCIONES ── */}
      <section id="funciones" className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl sm:text-3xl font-black text-slate-800 text-center">Todas las funciones, en ambos planes</h2>
        <p className="text-slate-500 text-center mt-2 text-sm">Sin funciones bloqueadas. Pruébalo todo gratis.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-10">
          {FUNCIONES.map(([Icon, t, d], i) => (
            <div key={i} className="bg-white rounded-2xl p-5 border border-slate-100 hover:border-navy-200 hover:shadow-md transition">
              <div className="w-10 h-10 bg-navy-50 rounded-xl flex items-center justify-center mb-3">
                <Icon className="w-5 h-5 text-navy-500" />
              </div>
              <p className="font-bold text-slate-700 text-sm">{t}</p>
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── PARA QUIÉN ── */}
      <section className="bg-slate-50 py-14">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-2xl font-black text-slate-800">Hecho para el que construye</h2>
          <div className="grid sm:grid-cols-3 gap-4 mt-8">
            {[
              ['👷', 'Maestros de obra', 'Cotiza reformas y remodelaciones con precios serios, sin depender de nadie'],
              ['🏠', 'Remodeladores', 'Cocinas, baños, ampliaciones — presupuesto profesional en la primera visita'],
              ['🏗️', 'Contratistas', 'Casas, locales, cubiertas — con contrato firmado antes de mover un ladrillo'],
            ].map(([e, t, d], i) => (
              <div key={i} className="bg-white rounded-2xl p-5 border border-slate-100">
                <span className="text-3xl">{e}</span>
                <p className="font-bold text-slate-700 mt-2 text-sm">{t}</p>
                <p className="text-xs text-slate-500 mt-1.5">{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CÓMO FUNCIONA ── */}
      <section id="como-funciona" className="max-w-5xl mx-auto px-4 py-16">
        <h2 className="text-2xl sm:text-3xl font-black text-slate-800 text-center">De cero a contrato firmado en 3 pasos</h2>
        <div className="grid sm:grid-cols-3 gap-6 mt-10">
          {[
            ['1', 'Arma el presupuesto', 'Busca actividades en la base APU, calcula cantidades por dimensiones y define tu AIU.'],
            ['2', 'Comparte por WhatsApp', 'Enlace profesional con tu logo. Ves cuándo lo abre y recibes su respuesta.'],
            ['3', 'El cliente firma', 'Contrato de obra civil con firma digital → PDF para ambos → a trabajar con respaldo.'],
          ].map(([n, t, d], i) => (
            <div key={i} className="text-center">
              <div className="w-12 h-12 bg-navy-800 text-white rounded-2xl flex items-center justify-center mx-auto font-black text-lg">{n}</div>
              <p className="font-bold text-slate-700 mt-4">{t}</p>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── PRICING ── */}
      <section id="precios" className="bg-navy-900 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-2xl sm:text-3xl font-black text-white text-center">Un solo diferencial: el volumen</h2>
          <p className="text-blue-300 text-center mt-2 text-sm">
            Ambos planes tienen TODAS las funciones. Pro es para quien cotiza sin parar.
          </p>

          <div className="grid sm:grid-cols-2 gap-5 mt-10 max-w-3xl mx-auto">
            {/* BÁSICO */}
            <div className="bg-white rounded-2xl p-7 flex flex-col">
              <p className="font-bold text-slate-700">Básico</p>
              <div className="mt-3">
                <span className="text-4xl font-black text-slate-800">$0</span>
                <span className="text-sm text-slate-400"> /siempre</span>
              </div>
              <p className="text-xs text-slate-400 mt-1.5">Para probar todo y cotizar de vez en cuando</p>
              <ul className="space-y-2.5 mt-6 flex-1">
                <CHECK bold>3 presupuestos al mes</CHECK>
                <CHECK>Todas las funciones de la herramienta</CHECK>
                <CHECK>Base APU 2026 + calculadora + AIU/IVA</CHECK>
                <CHECK>WhatsApp con visto, aceptar y rechazar</CHECK>
                <CHECK>Contrato de obra con firma digital</CHECK>
                <CHECK>Avances de obra + fotos + encuesta</CHECK>
                <CHECK>PDF y Excel con tu logo</CHECK>
              </ul>
              <Link to="/registro" className="mt-7 text-center border-2 border-navy-600 text-navy-600 font-bold text-sm py-3 rounded-xl hover:bg-navy-50 transition">
                Empezar gratis
              </Link>
            </div>

            {/* PRO */}
            <div className="bg-white rounded-2xl p-7 flex flex-col relative ring-4 ring-emerald-400">
              <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] font-black uppercase tracking-wider px-4 py-1.5 rounded-full">
                Para el que vive de esto
              </span>
              <p className="font-bold text-slate-700">Pro</p>
              <div className="mt-3 flex items-end gap-2">
                <span className="text-4xl font-black text-slate-800">$79.000</span>
                <span className="text-sm text-slate-400 pb-1.5">/mes</span>
              </div>
              <p className="text-xs text-slate-400 mt-1.5">Cotiza todo lo que tu negocio necesite</p>
              <ul className="space-y-2.5 mt-6 flex-1">
                <CHECK bold>Presupuestos ILIMITADOS</CHECK>
                <CHECK>Todas las funciones de la herramienta</CHECK>
                <CHECK>Base APU 2026 + calculadora + AIU/IVA</CHECK>
                <CHECK>WhatsApp con visto, aceptar y rechazar</CHECK>
                <CHECK>Contrato de obra con firma digital</CHECK>
                <CHECK>Avances de obra + fotos + encuesta</CHECK>
                <CHECK>Soporte prioritario por WhatsApp</CHECK>
              </ul>
              <Link to="/registro" className="mt-7 text-center bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-sm py-3 rounded-xl transition">
                Empezar con Pro
              </Link>
              <p className="text-[10px] text-slate-400 text-center mt-2">
                Una obra cerrada al año paga 3 años de Pro. La cuenta la haces tú.
              </p>
            </div>
          </div>
          <p className="text-center text-[11px] text-blue-400 mt-6">
            Precios en pesos colombianos · Cancela cuando quieras · Tus datos y proyectos siguen siendo tuyos
          </p>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="max-w-3xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-black text-slate-800 text-center mb-8">Preguntas frecuentes</h2>
        <div className="space-y-3">
          {[
            ['¿Qué diferencia hay entre Básico y Pro?', 'Solo una: el volumen. En Básico haces 3 presupuestos al mes con TODAS las funciones (contrato, avances, WhatsApp, todo). En Pro son ilimitados. Si cotizas más de 3 obras al mes, Pro se paga solo.'],
            ['¿Los precios de la base APU son confiables?', 'Son precios de referencia 2026 del mercado colombiano con factores por ciudad. Siempre puedes ajustar cualquier precio a tu realidad — tu ajuste queda guardado en el presupuesto.'],
            ['¿El contrato digital tiene validez?', 'Es un acuerdo privado con evidencia digital: nombre, documento, fecha y hora quedan registrados junto al texto íntegro. La Ley 527 de 1999 reconoce los mensajes de datos como medio de prueba en Colombia. Para obras con formalidades adicionales, consulta con tu abogado.'],
            ['¿Mi cliente necesita instalar algo?', 'Nada. Abre el enlace en su WhatsApp: ve el presupuesto, firma el contrato y sigue los avances desde el navegador de su celular.'],
            ['¿Cómo pago el plan Pro?', 'Por Nequi o transferencia Bancolombia desde la misma app. Reportas el pago y activamos tu Pro en menos de 24 horas.'],
            ['¿Qué pasa con mis datos si cancelo?', 'Son tuyos. Exportas todo a Excel y PDF, y tu cuenta Básica sigue activa con tus proyectos.'],
          ].map(([q, a], i) => (
            <details key={i} className="bg-slate-50 rounded-xl p-4 group">
              <summary className="font-semibold text-sm text-slate-700 cursor-pointer list-none flex justify-between items-center">
                {q} <ChevronRight className="w-4 h-4 text-slate-400 group-open:rotate-90 transition shrink-0 ml-2" />
              </summary>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* ── CTA FINAL ── */}
      <section className="bg-gradient-to-br from-navy-800 to-navy-600 py-16 text-center px-4">
        <h2 className="text-2xl sm:text-3xl font-black text-white">Tu próximo presupuesto, en 10 minutos</h2>
        <p className="text-blue-200 mt-3">Todas las funciones. Gratis. Sin tarjeta.</p>
        <Link to="/registro" className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-8 py-4 rounded-xl transition mt-7 text-sm">
          Crear mi cuenta gratis <ChevronRight className="w-4 h-4" />
        </Link>
      </section>

      {/* ── FOOTER ── */}
      <footer className="bg-navy-900 text-blue-300 text-xs py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-wrap justify-between gap-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            <span className="font-bold text-white">PresupuestarCO</span>
            <span>· Hecho en Colombia 🇨🇴</span>
          </div>
          <div className="flex gap-5">
            <a href="#funciones" className="hover:text-white transition">Funciones</a>
            <a href="#precios" className="hover:text-white transition">Precios</a>
            <Link to="/login" className="hover:text-white transition">Iniciar sesión</Link>
            <Link to="/registro" className="hover:text-white transition">Registrarse</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
