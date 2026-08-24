import { Link } from 'react-router-dom'

// ═══ TERMINOS Y POLITICA DE DATOS — borrador reforzado (version 18/8/2026) ═══
// NOTA INTERNA: este texto es un borrador tecnico-legal para revision de un
// abogado colombiano antes del cobro comercial. Cubre: rol de herramienta,
// Habeas Data (Ley 1581/2012) con roles responsable/encargado, retracto
// (Ley 1480), firma electronica (Ley 527/1999 + Dec. 2364/2012).

const S = ({ t, children }) => (
  <section className="mb-6">
    <h2 className="text-base font-black text-slate-800 mb-2">{t}</h2>
    <div className="text-[13px] text-slate-600 leading-relaxed space-y-2">{children}</div>
  </section>
)

export default function Legal() {
  return (
    <div className="min-h-screen bg-slate-50 py-10 px-5">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <Link to="/" className="text-[12px] text-navy-600 underline">← Volver</Link>
        <h1 className="text-2xl font-black text-slate-800 mt-3">Términos de servicio y política de tratamiento de datos</h1>
        <p className="text-[11px] text-slate-400 mt-1 mb-8">Versión del 18 de agosto de 2026 · PresupuestarCO</p>

        <S t="1. Qué es PresupuestarCO">
          <p>PresupuestarCO es una <strong>herramienta de apoyo</strong> para la elaboración de presupuestos de obra,
          seguimiento de proyectos y gestión comercial de contratistas de construcción en Colombia.
          La plataforma NO presta servicios de asesoría legal, contable ni tributaria.</p>
        </S>

        <S t="2. Los documentos generados son plantillas de referencia">
          <p>Los contratos, actas, cuentas de cobro y demás documentos que la plataforma genera son
          <strong> plantillas de referencia</strong> construidas con la información que el usuario ingresa.
          El usuario es responsable de revisarlas y adaptarlas a su caso concreto antes de usarlas.
          Los cálculos de IVA, AIU, retenciones y deducciones son <strong>ayudas de cálculo</strong> que no
          sustituyen la asesoría de un contador público.</p>
        </S>

        <S t="3. PresupuestarCO no es parte de los contratos de obra">
          <p>Los contratos de obra se celebran exclusivamente entre el usuario (contratista) y su cliente.
          PresupuestarCO no es parte de esos contratos, no garantiza su cumplimiento y no responde por la
          ejecución de las obras, la calidad de los trabajos ni los pagos entre las partes.</p>
        </S>

        <S t="4. Firma electrónica (Ley 527 de 1999)">
          <p>La aceptación de presupuestos y contratos mediante el enlace del cliente utiliza firma electrónica
          en los términos de la Ley 527 de 1999 y el Decreto 2364 de 2012. Como evidencia se conserva: la imagen
          de la firma, el nombre y documento declarados por el firmante, la dirección IP, y la fecha y hora exactas.</p>
        </S>

        <S t="5. Tratamiento de datos personales (Ley 1581 de 2012)">
          <p><strong>Datos de los usuarios:</strong> PresupuestarCO actúa como responsable del tratamiento de los
          datos de sus usuarios registrados (nombre, email, teléfono, documento, información comercial), que usa
          exclusivamente para operar la plataforma, emitir facturas y enviar comunicaciones del servicio.</p>
          <p><strong>Datos de los clientes de los usuarios:</strong> respecto de los datos que el usuario ingresa
          sobre sus propios clientes y firmantes (nombres, documentos, firmas), PresupuestarCO actúa como
          <strong> encargado</strong> del tratamiento por cuenta del usuario, quien es el responsable de contar
          con la autorización de sus clientes.</p>
          <p><strong>Derechos:</strong> conocer, actualizar, rectificar y suprimir los datos, y revocar la
          autorización, escribiendo al canal de soporte de la plataforma. Los datos se conservan mientras la
          cuenta esté activa y los plazos legales lo exijan.</p>
        </S>

        <S t="6. Planes, pagos y derecho de retracto">
          <p>El plan Gratis permite 3 presupuestos por mes. El plan Pro es una suscripción mensual pagada a
          través de Wompi (Bancolombia). Conforme a la Ley 1480 de 2011, el usuario puede ejercer el
          <strong> derecho de retracto dentro de los 5 días hábiles</strong> siguientes al pago, solicitando
          la devolución por el canal de soporte, siempre que aplique según la ley.</p>
        </S>

        <S t="7. Disponibilidad y respaldo">
          <p>La plataforma se ofrece "como está", con monitoreo automatizado y copias de seguridad periódicas.
          El usuario puede exportar su información (Excel, PDF) en cualquier momento. PresupuestarCO no garantiza
          disponibilidad ininterrumpida y no responde por perjuicios derivados de interrupciones del servicio.</p>
        </S>

        <S t="8. Contacto">
          <p>Canal de soporte disponible dentro de la plataforma. Este documento puede actualizarse;
          los cambios relevantes se notificarán a los usuarios registrados.</p>
        </S>
      </div>
    </div>
  )
}
