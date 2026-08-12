import React from 'react'
import { Link } from 'react-router-dom'
import { Building2, ArrowLeft } from 'lucide-react'

const H = ({ children }) => <h2 className="text-base font-bold text-slate-800 mt-8 mb-2">{children}</h2>
const P = ({ children }) => <p className="text-[13px] text-slate-500 leading-relaxed mb-3">{children}</p>

export default function Legal() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-navy-800 text-white">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link to="/" className="p-2 hover:bg-white/10 rounded-lg"><ArrowLeft className="w-4 h-4" /></Link>
          <span className="font-semibold flex items-center gap-2"><Building2 className="w-4 h-4" /> Términos y datos personales</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        <p className="text-[11px] text-slate-400 mb-6">Última actualización: agosto de 2026 · PresupuestarCO</p>

        <h1 className="text-lg font-black text-slate-800">Términos de servicio</h1>

        <H>1. Qué es PresupuestarCO</H>
        <P>PresupuestarCO es una herramienta de software para que contratistas de construcción en Colombia
        elaboren presupuestos, generen contratos y cuentas de cobro, registren avances y gastos de obra, y
        compartan esa información con sus clientes mediante enlaces. La herramienta genera documentos con base
        en la información que tú ingresas: <strong>no presta asesoría legal, contable ni tributaria</strong>,
        y eres responsable de verificar que tus documentos se ajusten a tu situación particular.</P>

        <H>2. Tu cuenta</H>
        <P>Eres responsable de la veracidad de tus datos, de mantener tu contraseña segura y de toda la
        actividad de tu cuenta. Debes ser mayor de edad. Podemos suspender cuentas que hagan uso fraudulento,
        abusivo o ilegal de la plataforma.</P>

        <H>3. Planes y pagos</H>
        <P>El plan Básico es gratuito con un límite mensual de presupuestos. El plan Pro tiene un cobro mensual
        (precio publicado en la página de precios) que habilita presupuestos ilimitados por 30 días desde cada
        activación. Los pagos en línea se procesan a través de Wompi (Grupo Bancolombia); no almacenamos datos
        de tarjetas. Si cancelas, conservas acceso Pro hasta el vencimiento del período pagado y luego tu
        cuenta pasa al plan Básico <strong>sin perder tus proyectos ni tu información</strong>.</P>

        <H>4. Tu contenido es tuyo</H>
        <P>Los presupuestos, contratos, fotos, firmas y datos que creas te pertenecen. Nos autorizas a
        almacenarlos y procesarlos únicamente para prestarte el servicio (por ejemplo, generar tus PDF o
        mostrar el avance a tu cliente en el enlace que tú compartes). Puedes exportar tu información a
        PDF y Excel en cualquier momento.</P>

        <H>5. Documentos con firma electrónica</H>
        <P>Los contratos y actas incorporan firma electrónica con registro de nombre, documento, trazo, fecha y
        hora, al amparo de la Ley 527 de 1999 sobre mensajes de datos y firmas electrónicas. La validez y los
        efectos de cada contrato entre tú y tu cliente dependen de las circunstancias de cada caso y son
        responsabilidad de las partes que lo suscriben.</P>

        <H>6. Disponibilidad y responsabilidad</H>
        <P>Prestamos el servicio "tal cual", con el máximo cuidado pero sin garantía de disponibilidad
        ininterrumpida. En la medida permitida por la ley, nuestra responsabilidad se limita al valor pagado
        por ti en los últimos 3 meses. Te recomendamos exportar copias de tus documentos importantes.</P>

        <H>7. Cambios</H>
        <P>Podemos actualizar estos términos; si el cambio es relevante te lo informaremos dentro de la
        aplicación. El uso continuado tras el aviso constituye aceptación.</P>

        <h1 className="text-lg font-black text-slate-800 mt-12">Política de tratamiento de datos personales</h1>
        <P>En cumplimiento de la Ley 1581 de 2012 y el Decreto 1377 de 2013 (habeas data).</P>

        <H>1. Responsable y encargado</H>
        <P><strong>Sobre tus datos</strong> (tu nombre, correo, teléfono, documento, firma y datos de tu
        negocio): PresupuestarCO actúa como responsable del tratamiento. Contacto para asuntos de datos:
        el canal de soporte dentro de la aplicación o el correo indicado en la sección de soporte.</P>
        <P><strong>Sobre los datos de TUS clientes</strong> (nombre, teléfono, documento y firma que tú
        registras al cotizar y contratar): tú eres el responsable de contar con su autorización;
        PresupuestarCO actúa como encargado del tratamiento, procesándolos exclusivamente según tus
        instrucciones para generar tus documentos y enlaces.</P>

        <H>2. Qué datos tratamos y para qué</H>
        <P>Datos de cuenta (identificación y contacto) para prestarte el servicio y comunicarnos contigo;
        datos de tus proyectos (presupuestos, contratos, avances, fotos, gastos, cuentas de cobro y firmas)
        para generar tus documentos y las vistas de tus clientes; datos de pago del plan Pro (procesados por
        Wompi — no almacenamos tarjetas). No vendemos ni compartimos tus datos con terceros para publicidad.</P>

        <H>3. Tus derechos (y los de tus clientes)</H>
        <P>Conocer, actualizar, rectificar y suprimir los datos, solicitar prueba de la autorización y
        revocarla. Puedes ejercerlos desde tu perfil o escribiendo por el canal de soporte; respondemos en
        los términos de la ley (10 a 15 días hábiles). Si tu cliente te solicita la supresión de sus datos,
        puedes eliminar el proyecto correspondiente o pedirnos apoyo por soporte.</P>

        <H>4. Seguridad y conservación</H>
        <P>Los datos se almacenan cifrados en tránsito, con contraseñas protegidas mediante hash y acceso
        restringido. Conservamos tu información mientras tu cuenta exista; al solicitar la eliminación de tu
        cuenta, suprimimos tus datos personales salvo los que la ley nos obligue a retener.</P>

        <H>5. Transferencias</H>
        <P>La infraestructura utiliza proveedores de nube (alojamiento y base de datos) que pueden operar
        fuera de Colombia bajo estándares de seguridad reconocidos, únicamente para la prestación del
        servicio.</P>

        <div className="mt-10 text-center">
          <Link to="/registro" className="text-sm text-navy-600 font-medium">← Volver al registro</Link>
        </div>
      </main>
    </div>
  )
}
