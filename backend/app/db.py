# -*- coding: utf-8 -*-
"""Base de datos SQLite — simple, confiable, cero configuracion."""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime, timezone

# Postgres en produccion (Vercel/Neon via DATABASE_URL), SQLite en local
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""

if DATABASE_URL:
    # Normalizar scheme: Neon/Vercel dan postgres:// pero SQLAlchemy quiere postgresql://
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=3)
    ES_POSTGRES = True
else:
    DB_PATH = os.environ.get("DB_PATH", "/app/data_db/presupuestar.db")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    ES_POSTGRES = False
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    nombre = Column(String(120), nullable=False)
    empresa = Column(String(160), default="")
    telefono = Column(String(30), default="")
    ciudad = Column(String(60), default="bogota")
    logo_b64 = Column(Text, default="")          # logo en base64 para PDF/Excel
    condiciones = Column(Text, default="")       # condiciones estandar auto-incluidas
    documento = Column(String(30), default="")   # cedula/NIT del contratista (para el contrato)
    pago_info = Column(String(200), default="")  # cuenta bancaria para forma de pago
    plan = Column(String(20), default="gratis")  # gratis | pro
    plan_vence = Column(DateTime, nullable=True)  # cuando expira el plan pro
    presupuestos_mes = Column(Integer, default=0)
    mes_actual = Column(String(7), default="")   # "2026-08" para reset mensual
    creado = Column(DateTime, default=utcnow)


class Proyecto(Base):
    __tablename__ = "proyectos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    numero = Column(String(30), default="", index=True)   # COT-2026-0001
    nombre = Column(String(200), nullable=False)
    cliente_nombre = Column(String(160), default="")
    cliente_telefono = Column(String(30), default="")
    direccion = Column(String(250), default="")
    region = Column(String(60), default="bogota")
    estado = Column(String(20), default="borrador")  # borrador | enviado | aceptado
    items_json = Column(Text, default="[]")     # lista de items del presupuesto
    aiu_json = Column(Text, default='{"admin":15,"imprevistos":5,"utilidad":8,"aplicar":true,"iva_sobre_utilidad":true}')
    notas = Column(Text, default="")
    contrato_json = Column(Text, default="{}")  # {plazo_dias, anticipo_pct, fecha_inicio, lugar}
    share_token = Column(String(40), unique=True, index=True, nullable=True)
    creado = Column(DateTime, default=utcnow)
    actualizado = Column(DateTime, default=utcnow, onupdate=utcnow)


class EventoShare(Base):
    __tablename__ = "eventos_share"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # visto | aceptado | rechazado
    nombre_firma = Column(String(160), default="")     # quien firma la aceptacion
    documento_firma = Column(String(30), default="")   # cedula/NIT del firmante
    user_agent = Column(String(300), default="")
    creado = Column(DateTime, default=utcnow)


class TicketSoporte(Base):
    __tablename__ = "tickets_soporte"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    asunto = Column(String(200), nullable=False)
    descripcion = Column(Text, default="")
    contexto = Column(String(300), default="")   # pagina, plan, navegador
    fotos_json = Column(Text, default="[]")      # evidencia (max 2 imagenes base64)
    estado = Column(String(20), default="abierto")  # abierto | resuelto
    respuesta = Column(Text, default="")            # respuesta del equipo de soporte
    email_enviado = Column(Boolean, default=False)
    creado = Column(DateTime, default=utcnow)
    respondido = Column(DateTime, nullable=True)


class SolicitudPro(Base):
    __tablename__ = "solicitudes_pro"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    metodo = Column(String(30), default="nequi")      # nequi | bancolombia | otro
    referencia = Column(String(120), default="")      # nro de comprobante que reporta el usuario
    estado = Column(String(20), default="pendiente")  # pendiente | aprobada | rechazada
    creado = Column(DateTime, default=utcnow)
    resuelto = Column(DateTime, nullable=True)


class Encuesta(Base):
    __tablename__ = "encuestas"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, unique=True, index=True)
    estrellas = Column(Integer, default=0)          # 1-5
    recomendaria = Column(Boolean, default=True)
    comentario = Column(Text, default="")
    creado = Column(DateTime, default=utcnow)


class Avance(Base):
    __tablename__ = "avances"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    titulo = Column(String(160), nullable=False)
    descripcion = Column(Text, default="")
    porcentaje = Column(Integer, default=0)        # avance ponderado por valor 0-100
    valor_ejecutado = Column(Integer, default=0)   # $ ejecutado segun % por actividad
    items_json = Column(Text, default="[]")        # detalle por actividad: [{id, descripcion, valor_item, pct, valor_ejec}]
    fotos_json = Column(Text, default="[]")        # lista de fotos base64 (max 3)
    creado = Column(DateTime, default=utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Migracion simple: agregar columnas nuevas a BDs existentes
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            if ES_POSTGRES:
                for sql in [
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS condiciones TEXT DEFAULT ''",
                    "ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS numero VARCHAR(30) DEFAULT ''",
                    "ALTER TABLE eventos_share ADD COLUMN IF NOT EXISTS nombre_firma VARCHAR(160) DEFAULT ''",
                    "ALTER TABLE eventos_share ADD COLUMN IF NOT EXISTS documento_firma VARCHAR(30) DEFAULT ''",
                    "ALTER TABLE avances ADD COLUMN IF NOT EXISTS valor_ejecutado INTEGER DEFAULT 0",
                    "ALTER TABLE avances ADD COLUMN IF NOT EXISTS items_json TEXT DEFAULT '[]'",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS documento VARCHAR(30) DEFAULT ''",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS pago_info VARCHAR(200) DEFAULT ''",
                    "ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS contrato_json TEXT DEFAULT '{}'",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS plan_vence TIMESTAMP",
                    "ALTER TABLE tickets_soporte ADD COLUMN IF NOT EXISTS respuesta TEXT DEFAULT ''",
                    "ALTER TABLE tickets_soporte ADD COLUMN IF NOT EXISTS respondido TIMESTAMP",
                ]:
                    conn.execute(text(sql))
                conn.commit()
            else:
                migs = [
                    ("usuarios", "condiciones", "ALTER TABLE usuarios ADD COLUMN condiciones TEXT DEFAULT ''"),
                    ("proyectos", "numero", "ALTER TABLE proyectos ADD COLUMN numero VARCHAR(30) DEFAULT ''"),
                    ("eventos_share", "nombre_firma", "ALTER TABLE eventos_share ADD COLUMN nombre_firma VARCHAR(160) DEFAULT ''"),
                    ("eventos_share", "documento_firma", "ALTER TABLE eventos_share ADD COLUMN documento_firma VARCHAR(30) DEFAULT ''"),
                    ("avances", "valor_ejecutado", "ALTER TABLE avances ADD COLUMN valor_ejecutado INTEGER DEFAULT 0"),
                    ("avances", "items_json", "ALTER TABLE avances ADD COLUMN items_json TEXT DEFAULT '[]'"),
                    ("usuarios", "documento", "ALTER TABLE usuarios ADD COLUMN documento VARCHAR(30) DEFAULT ''"),
                    ("usuarios", "pago_info", "ALTER TABLE usuarios ADD COLUMN pago_info VARCHAR(200) DEFAULT ''"),
                    ("proyectos", "contrato_json", "ALTER TABLE proyectos ADD COLUMN contrato_json TEXT DEFAULT '{}'"),
                    ("usuarios", "plan_vence", "ALTER TABLE usuarios ADD COLUMN plan_vence TIMESTAMP"),
                    ("tickets_soporte", "respuesta", "ALTER TABLE tickets_soporte ADD COLUMN respuesta TEXT DEFAULT ''"),
                    ("tickets_soporte", "respondido", "ALTER TABLE tickets_soporte ADD COLUMN respondido TIMESTAMP"),
                ]
                for tabla, col, sql in migs:
                    cols = [r[1] for r in conn.execute(text(f"PRAGMA table_info({tabla})"))]
                    if col not in cols:
                        conn.execute(text(sql))
                conn.commit()
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
