import React from 'react'
import { Link } from 'react-router-dom'
import { Building2, Search, MessageCircle, FileSignature, HardHat, Calculator,
         CheckCircle2, Zap, Shield, TrendingUp, ChevronRight, Star } from 'lucide-react'

const CHECK = ({ children }) => (
  <li className="flex items-start gap-2.5 text-sm text-slate-600">
    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
    <span>{children}</span>
  </li>
)

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── NAV ── */}
      <nav className="sticky top-0 z-50 bg-navy-800/95 backdrop-blur border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
              <Building2 className="w-4.5 h-4.5 text-white w-5 h-5" />
            </div>
            <span className="font-bold text-white">PresupuestarCO</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="#precios" className="hidden sm:block text-sm text-blue-200 hover:text-white transition">Precios</a>
            <a href="#como-funciona" className="hidden sm:block text-sm text-blue-200 hover:text-white transition">Cómo funciona</a>
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
              <Zap className="w-3.5 h-3.5" /> Lanzamiento: todo gratis por tiempo limitado
            </span>
            <h1 className="text-4xl sm:text-5xl font-black leading-tight tracking-tight">
              Presupuestos de obra profesionales <span className="text-emerald-400">en minutos</span>, no en madrugadas
            </h1>
            <p className="text-lg text-blue-200 mt-5 leading-relaxed">
              La herramienta del contratista colombiano: base APU 2026 con 2.288 actividades,
              AIU e IVA calculados como manda la ley, y tu cliente firma el contrato
              directo desde WhatsApp.
            </p>
            <div className="flex flex-wrap gap-3 mt-8">
              <Link to="/registro" className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-6 py-3.5 rounded-xl transition text-sm">
                Crear cuenta gratis <ChevronRight className="w-4 h-4" />
              </Link>
              <a href="#como-funciona" className="flex items-center gap-2 border border-white/20 hover:bg-white/5 text-white font-medium px-6 py-3.5 rounded-xl transition text-sm">
                Ver cómo funciona
              </a>
            </div>
            <p className="text-xs text-blue-300 mt-4">Sin tarjeta de crédito · Listo en 2 minutos</p>
          </div>

          {/* Mini mockup */}
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

      {/* ── FEATURES ── */}
      <section className="bg-slate-50 py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-2xl sm:text-3xl font-black text-slate-800 text-center">Todo lo que necesitas para cotizar y cobrar</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-10">
            {[
              [Search, 'Base APU 2026', '2.288 actividades con precios de referencia colombianos, por capítulos, con factores para 13 ciudades.'],
              [Calculator, 'Calculadora de cantidades', '¿3 columnas de 30×30 por 3 metros? La app convierte a m³ sola. Volumen, área y metros lineales.'],
              [Shield, 'AIU e IVA como manda la ley', 'IVA 19% solo sobre la utilidad (Art. 462-1 ET, contratos de construcción). Deja de regalar plata al calcular mal.'],
              [MessageCircle, 'WhatsApp con "visto"', 'Tu cliente abre el presupuesto en su celular. Tú ves cuándo lo abrió, cuántas veces y si aceptó.'],
              [FileSignature, 'Contrato de obra civil', 'Al aceptar, el cliente firma un Contrato de Ejecución de Obra generado automático: cláusulas, plazos, anticipo, todo.'],
              [HardHat, 'Avances de obra con $$', 'Marca el % por actividad y el cliente ve el valor ejecutado en tiempo real. Fotos incluidas. Se acabaron las discusiones.'],
            ].map(([Icon, t, d], i) => (
              <div key={i} className="bg-white rounded-2xl p-5 border border-slate-100 hover:border-navy-200 hover:shadow-md transition">
                <div className="w-10 h-10 bg-navy-50 rounded-xl flex items-center justify-center mb-3">
                  <Icon className="w-5 h-5 text-navy-500" />
                </div>
                <p className="font-bold text-slate-700 text-sm">{t}</p>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{d}</p>
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
            ['1', 'Arma el presupuesto', 'Busca las actividades en la base APU, ajusta cantidades con la calculadora y define tu AIU.'],
            ['2', 'Comparte por WhatsApp', 'Un enlace profesional con tu logo. Ves cuándo lo abre y recibes su respuesta.'],
            ['3', 'El cliente firma el contrato', 'Acepta con nombre y cédula → contrato de obra civil en PDF para ambos. A trabajar.'],
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
          <h2 className="text-2xl sm:text-3xl font-black text-white text-center">Precios simples, sin letra pequeña</h2>
          <p className="text-blue-300 text-center mt-2 text-sm">Empieza gratis. Crece cuando tu negocio crezca.</p>

          <div className="grid sm:grid-cols-2 gap-5 mt-10 max-w-3xl mx-auto">
            {/* BÁSICO */}
            <div className="bg-white rounded-2xl p-7 flex flex-col">
              <p className="font-bold text-slate-700">Básico</p>
              <div className="mt-3">
                <span className="text-4xl font-black text-slate-800">$0</span>
              </div>
              <p className="text-xs text-slate-400 mt-1.5">Para probar y cotizar de vez en cuando</p>
              <ul className="space-y-2.5 mt-6 flex-1">
                <CHECK>3 presupuestos al mes</CHECK>
                <CHECK>Base APU 2026 completa (2.288 actividades)</CHECK>
                <CHECK>Calculadora de cantidades</CHECK>
                <CHECK>AIU + IVA sobre utilidad</CHECK>
                <CHECK>Enlace WhatsApp con "visto"</CHECK>
                <CHECK>PDF y Excel (con marca de agua)</CHECK>
              </ul>
              <Link to="/registro" className="mt-7 text-center border-2 border-navy-600 text-navy-600 font-bold text-sm py-3 rounded-xl hover:bg-navy-50 transition">
                Empezar gratis
              </Link>
            </div>

            {/* PRO */}
            <div className="bg-white rounded-2xl p-7 flex flex-col relative ring-4 ring-emerald-400">
              <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] font-black uppercase tracking-wider px-4 py-1.5 rounded-full">
                Más popular
              </span>
              <p className="font-bold text-slate-700">Pro</p>
              <div className="mt-3 flex items-end gap-2">
                <span className="text-4xl font-black text-slate-800">$79.000</span>
                <span className="text-sm text-slate-400 pb-1.5">/mes</span>
              </div>
              <p className="text-xs text-slate-400 mt-1.5">Para el contratista que vive de esto</p>
              <ul className="space-y-2.5 mt-6 flex-1">
                <CHECK><strong>Presupuestos ilimitados</strong></CHECK>
                <CHECK>Todo lo del plan Básico</CHECK>
                <CHECK>Tu logo en PDFs y enlaces (sin marca de agua)</CHECK>
                <CHECK>Contrato de Ejecución de Obra Civil con firma digital</CHECK>
                <CHECK>Avances de obra con valor ejecutado y fotos</CHECK>
                <CHECK>Encuesta de satisfacción y calificaciones ⭐</CHECK>
                <CHECK>Soporte prioritario por WhatsApp</CHECK>
              </ul>
              <Link to="/registro" className="mt-7 text-center bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-sm py-3 rounded-xl transition">
                Empezar con Pro
              </Link>
              <p className="text-[10px] text-slate-400 text-center mt-2">🎉 Gratis durante el lanzamiento</p>
            </div>
          </div>
          <p className="text-center text-[11px] text-blue-400 mt-6">
            Precios en pesos colombianos. Cancela cuando quieras — tus datos y proyectos siguen siendo tuyos.
          </p>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="max-w-3xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-black text-slate-800 text-center mb-8">Preguntas frecuentes</h2>
        <div className="space-y-3">
          {[
            ['¿Los precios de la base APU son confiables?', 'Son precios de referencia 2026 del mercado colombiano con factores por ciudad. Siempre puedes ajustar cualquier precio a tu realidad — y tu ajuste queda guardado en el presupuesto.'],
            ['¿El contrato digital tiene validez?', 'Es un acuerdo privado con evidencia digital: nombre, documento, fecha y hora quedan registrados junto al texto íntegro del contrato. La Ley 527 de 1999 reconoce los mensajes de datos como medio de prueba en Colombia. Para obras que requieran formalidades adicionales, consulta con tu abogado.'],
            ['¿Mi cliente necesita instalar algo o crear cuenta?', 'Nada. Abre el enlace en su WhatsApp y listo: ve el presupuesto, firma el contrato y sigue los avances de su obra desde el navegador de su celular.'],
            ['¿Qué pasa con mis datos si cancelo?', 'Son tuyos. Puedes exportar todos tus presupuestos a Excel y PDF antes de irte, y tu cuenta gratis sigue activa con tus proyectos.'],
            ['¿Sirve para obras grandes con interventoría?', 'Está optimizado para el contratista pequeño y mediano: reformas, casas, locales, cubiertas. Para licitaciones públicas con requisitos especiales, úsalo como base y complementa según el pliego.'],
          ].map(([q, a], i) => (
            <details key={i} className="bg-slate-50 rounded-xl p-4 group">
              <summary className="font-semibold text-sm text-slate-700 cursor-pointer list-none flex justify-between items-center">
                {q} <ChevronRight className="w-4 h-4 text-slate-400 group-open:rotate-90 transition" />
              </summary>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* ── CTA FINAL ── */}
      <section className="bg-gradient-to-br from-navy-800 to-navy-600 py-16 text-center px-4">
        <h2 className="text-2xl sm:text-3xl font-black text-white">Tu próximo presupuesto, en 10 minutos</h2>
        <p className="text-blue-200 mt-3">Únete a los contratistas que ya cotizan como profesionales.</p>
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
            <a href="#precios" className="hover:text-white transition">Precios</a>
            <Link to="/login" className="hover:text-white transition">Iniciar sesión</Link>
            <Link to="/registro" className="hover:text-white transition">Registrarse</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
