import React from 'react'
import { Link } from 'react-router-dom'
import { Building2, ArrowLeft } from 'lucide-react'

const H = ({ children }) => <h2 className="text-base font-bold text-slate-800 mt-8 mb-2">{children}</h2>
const P = ({ children }) => <p className="text-[13px] text-slate-500 leading-relaxed mb-3">{children}</p>
const NORMA = ({ children }) => <span className="text-[11px] text-slate-400 italic">({children})</span>

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
        <p className="text-[11px] text-slate-400 mb-6">
          Versión 2.0 · Vigente desde agosto de 2026 · PresupuestarCO<br />
          Marco normativo principal: Ley Estatutaria 1581 de 2012, Decreto 1377 de 2013 (compilado en el
          Decreto Único 1074 de 2015), Decreto 090 de 2018, Circular Única de la SIC (Título V),
          Ley 527 de 1999, Decreto 2364 de 2012 y Ley 1480 de 2011 (Estatuto del Consumidor).
        </p>

        <h1 className="text-lg font-black text-slate-800">Términos de servicio</h1>

        <H>1. Naturaleza del servicio</H>
        <P>PresupuestarCO es una <strong>herramienta de software de gestión documental y administrativa</strong> para
        contratistas de construcción en Colombia: elaboración de presupuestos con base de precios de referencia,
        generación de plantillas de contrato, cuentas de cobro, otrosíes y actas, registro de avances y gastos,
        y publicación de un enlace informativo para el cliente de cada obra. Los documentos se generan con la
        información que ingresa el usuario. <strong>PresupuestarCO no presta asesoría legal, contable, tributaria
        ni de ingeniería</strong>; los precios de referencia son estimativos y cada usuario es responsable de
        verificar que sus documentos y valores se ajusten a su caso particular.</P>

        <H>2. Posición neutral de la plataforma</H>
        <P>Todo contrato de obra, otrosí o acta que se firme a través de la plataforma es un negocio jurídico
        celebrado <strong>exclusivamente entre el contratista y su cliente</strong>, quienes son sus únicas partes
        y a quienes obliga como ley entre ellas <NORMA>art. 1602 del Código Civil</NORMA>. PresupuestarCO
        <strong> no es parte, garante, interventor ni árbitro</strong> de esos negocios; actúa como proveedor
        tecnológico neutral que genera, almacena y conserva los documentos y sus registros de trazabilidad
        (fecha, hora, identificación del firmante, dirección IP y dispositivo), los cuales pueden servir como
        elemento probatorio para las partes <NORMA>arts. 10 y 11, Ley 527 de 1999</NORMA>.</P>

        <H>3. Firma electrónica y valor probatorio</H>
        <P>Las firmas incorporadas en los documentos de la plataforma constituyen <strong>firma electrónica</strong> en
        los términos del Decreto 2364 de 2012: métodos como el trazo manuscrito digitalizado, la identificación
        con nombre y documento, y los códigos y registros técnicos asociados, que permiten identificar al
        firmante y su intención de aprobar el contenido, con la confiabilidad apropiada a los fines del mensaje.
        La ley reconoce a los mensajes de datos plenos efectos jurídicos, validez y fuerza probatoria en virtud
        del principio de <strong>equivalencia funcional</strong> <NORMA>arts. 5 a 10, Ley 527 de 1999</NORMA>.
        La eficacia concreta de cada contrato depende de sus propias circunstancias y de la capacidad y
        consentimiento de las partes que lo suscriben.</P>

        <H>4. Cuenta del usuario</H>
        <P>El usuario declara ser mayor de edad y responsable de la veracidad de su información, de la custodia
        de sus credenciales y de la actividad de su cuenta. Nos reservamos el derecho de suspender cuentas que
        hagan uso fraudulento, abusivo o contrario a la ley, incluido el uso de la plataforma para tratar datos
        de terceros sin autorización.</P>

        <H>5. Planes, pagos, retracto y reversión</H>
        <P>El plan Básico es gratuito con límite mensual de presupuestos. El plan Pro tiene cobro mensual
        (precio publicado) procesado por Wompi S.A.S. (vigilada por la Superintendencia Financiera); no
        almacenamos datos de tarjetas. Al cancelar, el acceso Pro continúa hasta el fin del período pagado y la
        cuenta pasa al plan Básico <strong>sin pérdida de proyectos ni información</strong>. En ventas a
        distancia, el consumidor puede ejercer el <strong>derecho de retracto dentro de los cinco (5) días
        hábiles</strong> siguientes a la compra, con devolución del dinero <NORMA>art. 47, Ley 1480 de 2011</NORMA>,
        y solicitar la <strong>reversión del pago</strong> en los casos del art. 51 de la misma ley (fraude,
        operación no solicitada, entre otros), ante su emisor y con aviso a nosotros.</P>

        <H>6. Propiedad intelectual y contenido</H>
        <P>El software, su código, diseño, marca y base de conocimiento pertenecen a PresupuestarCO y están
        protegidos por la Ley 23 de 1982 y la Decisión Andina 351 de 1993. El usuario recibe una licencia de
        uso personal, no exclusiva e intransferible. <strong>El contenido creado por el usuario (presupuestos,
        contratos, fotos, firmas, datos de obra) es y seguirá siendo del usuario</strong>; nos autoriza a
        almacenarlo y procesarlo únicamente para prestar el servicio, y puede exportarlo en PDF y Excel en
        cualquier momento.</P>

        <H>7. Disponibilidad y limitación de responsabilidad</H>
        <P>El servicio se presta "tal cual" y "según disponibilidad", con esfuerzos razonables de continuidad,
        copias de seguridad periódicas y medidas de seguridad, pero sin garantía de disponibilidad
        ininterrumpida. En la máxima medida permitida por la ley colombiana, la responsabilidad total de
        PresupuestarCO se limita al valor efectivamente pagado por el usuario en los tres (3) meses anteriores
        al hecho. Nada de lo aquí previsto limita responsabilidades que por ley no puedan excluirse.</P>

        <H>8. Encargo de tratamiento (cláusula de transmisión)</H>
        <P>Al usar la plataforma para registrar datos de sus clientes, <strong>el contratista actúa como
        Responsable del Tratamiento y PresupuestarCO como Encargado</strong> <NORMA>art. 3, lits. d) y e),
        Ley 1581 de 2012</NORMA>. Esta cláusula constituye el contrato de transmisión previsto en la
        regulación <NORMA>art. 25, Decreto 1377 de 2013, compilado en el Decreto 1074 de 2015</NORMA>:
        PresupuestarCO tratará dichos datos únicamente conforme a las instrucciones del Responsable derivadas
        del uso de la herramienta, con los deberes del art. 18 de la Ley 1581 (seguridad, confidencialidad,
        atención de consultas y reclamos, y aviso al Responsable ante incidentes). El contratista declara
        contar con la autorización de sus clientes o recabarla mediante los mecanismos que la plataforma
        dispone al momento de la firma.</P>

        <H>9. Ley aplicable, cambios y contacto</H>
        <P>Estos términos se rigen por la ley de la República de Colombia. Podemos actualizarlos; los cambios
        relevantes se notificarán en la aplicación con su nueva versión y fecha, y el uso posterior constituye
        aceptación. Notificaciones: el canal de soporte de la aplicación.</P>

        <h1 className="text-lg font-black text-slate-800 mt-12">Política de tratamiento de datos personales</h1>
        <P>Adoptada en cumplimiento de la Ley Estatutaria 1581 de 2012 y su reglamentación
        <NORMA> Decreto 1377 de 2013, compilado en el Decreto 1074 de 2015</NORMA>.</P>

        <H>1. Roles: responsable y encargado</H>
        <P><strong>Datos del contratista usuario</strong> (nombre, correo, teléfono, documento, firma, datos del
        negocio y de facturación): PresupuestarCO es el <strong>Responsable del Tratamiento</strong>.</P>
        <P><strong>Datos de los clientes del contratista</strong> (nombre, documento, teléfono, firma manuscrita
        digitalizada, dirección de la obra, y registros técnicos de sus interacciones): el contratista es el
        <strong> Responsable</strong> y PresupuestarCO el <strong>Encargado</strong>, conforme a la cláusula 8
        de los Términos.</P>

        <H>2. Finalidades</H>
        <P>(i) Prestar el servicio: crear, firmar, conservar y exhibir los documentos de cada obra y sus enlaces;
        (ii) trazabilidad y prueba de las firmas y eventos (fecha, hora, IP, dispositivo)
        <NORMA>art. 8, Decreto 1377 de 2013 — prueba de la autorización</NORMA>; (iii) comunicaciones
        operativas del servicio; (iv) facturación del plan Pro; (v) seguridad, prevención de fraude y
        cumplimiento legal. <strong>No vendemos datos ni los compartimos con terceros para publicidad.</strong>
        No tratamos datos de menores de edad ni datos sensibles como finalidad del servicio.</P>

        <H>3. Autorización</H>
        <P>La autorización se obtiene de forma previa, expresa e informada, por escrito o mediante
        <strong> conductas inequívocas</strong> del titular que permiten concluir razonablemente que la otorgó
        — como firmar con nombre y documento bajo el aviso de privacidad visible en cada punto de firma; el
        silencio nunca se asimila a autorización <NORMA>art. 7, Decreto 1377 de 2013</NORMA>. Conservamos
        prueba de cada autorización con sus registros técnicos <NORMA>art. 8, ibídem</NORMA>. El aviso de
        privacidad se difunde por este medio electrónico <NORMA>arts. 14 a 17, ibídem</NORMA>.</P>

        <H>4. Derechos de los titulares y procedimiento</H>
        <P>Todo titular puede conocer, actualizar, rectificar y suprimir sus datos, solicitar prueba de la
        autorización, revocarla y presentar quejas ante la SIC <NORMA>art. 8, Ley 1581 de 2012</NORMA>.
        Canal: el soporte dentro de la aplicación (o el correo publicado en la sección de soporte).
        <strong> Consultas</strong>: respuesta en máximo diez (10) días hábiles, prorrogables por cinco (5)
        informando la causa <NORMA>art. 14</NORMA>. <strong>Reclamos</strong>: leyenda "reclamo en trámite"
        dentro de los dos (2) días hábiles y respuesta en máximo quince (15) días hábiles, prorrogables por
        ocho (8) <NORMA>art. 15</NORMA>. La queja ante la SIC procede una vez agotado este trámite
        <NORMA>art. 16</NORMA>. Si un cliente final ejerce derechos ante su contratista, prestamos al
        Responsable el apoyo necesario como Encargado.</P>

        <H>5. Transferencia y transmisión internacional</H>
        <P>La infraestructura de la plataforma (alojamiento y base de datos) opera en los
        <strong> Estados Unidos de América</strong>, país incluido por la Superintendencia de Industria y
        Comercio en la lista de países con <strong>nivel adecuado de protección de datos</strong>
        <NORMA>numeral 3.2, Capítulo Tercero, Título V de la Circular Única — Circular Externa 005 de 2017</NORMA>,
        por lo que la operación está permitida por el art. 26 de la Ley 1581 de 2012. En virtud del principio
        de <strong>responsabilidad demostrada</strong>, mantenemos medidas apropiadas y verificables:
        cifrado en tránsito, contraseñas con hash, controles de acceso por autenticación, límites y registros
        de auditoría, copias de seguridad periódicas y pruebas automatizadas de seguridad en cada
        actualización.</P>

        <H>6. Registro Nacional de Bases de Datos (RNBD)</H>
        <P>El deber de inscripción en el RNBD aplica a sociedades con activos totales superiores a 100.000 UVT
        <NORMA>Decreto 090 de 2018</NORMA>. Mientras no se supere dicho umbral, PresupuestarCO no está obligada
        al registro, sin perjuicio del cumplimiento íntegro de las demás obligaciones de la Ley 1581 de 2012,
        incluida esta política. Superado el umbral, las bases se inscribirán en los plazos reglamentarios.</P>

        <H>7. Seguridad, conservación y supresión</H>
        <P>Aplicamos el principio de seguridad <NORMA>art. 4, lit. g), Ley 1581 de 2012</NORMA> con las medidas
        descritas en el numeral 5. Conservamos la información mientras la cuenta exista y por el tiempo
        razonable y necesario según las finalidades y los deberes contables, fiscales y legales
        <NORMA>art. 11, Decreto 1377 de 2013</NORMA>. Ante la solicitud de supresión, se eliminan o anonimizan
        los datos personales, salvo aquellos que deban conservarse por deber legal o contractual — por ejemplo,
        documentos firmados en los que un tercero también es titular de derechos.</P>

        <H>8. Vigencia</H>
        <P>Esta política rige desde su publicación y permanece vigente mientras se realice tratamiento de
        datos personales. Versión 2.0 — agosto de 2026.</P>

        <div className="mt-10 text-center">
          <Link to="/registro" className="text-sm text-navy-600 font-medium">← Volver al registro</Link>
        </div>
      </main>
    </div>
  )
}
