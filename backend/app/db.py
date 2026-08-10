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
    plan = Column(String(20), default="gratis")  # gratis | pro | pro_ia
    presupuestos_mes = Column(Integer, default=0)
    mes_actual = Column(String(7), default="")   # "2026-08" para reset mensual
    creado = Column(DateTime, default=utcnow)


class Proyecto(Base):
    __tablename__ = "proyectos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    cliente_nombre = Column(String(160), default="")
    cliente_telefono = Column(String(30), default="")
    direccion = Column(String(250), default="")
    region = Column(String(60), default="bogota")
    estado = Column(String(20), default="borrador")  # borrador | enviado | aceptado
    items_json = Column(Text, default="[]")     # lista de items del presupuesto
    aiu_json = Column(Text, default='{"admin":15,"imprevistos":5,"utilidad":8,"aplicar":true,"iva_sobre_utilidad":true}')
    notas = Column(Text, default="")
    share_token = Column(String(40), unique=True, index=True, nullable=True)
    creado = Column(DateTime, default=utcnow)
    actualizado = Column(DateTime, default=utcnow, onupdate=utcnow)


class EventoShare(Base):
    __tablename__ = "eventos_share"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # visto | aceptado
    user_agent = Column(String(300), default="")
    creado = Column(DateTime, default=utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Migracion simple: agregar columnas nuevas a BDs existentes
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            if ES_POSTGRES:
                conn.execute(text(
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS condiciones TEXT DEFAULT ''"
                ))
                conn.commit()
            else:
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(usuarios)"))]
                if "condiciones" not in cols:
                    conn.execute(text("ALTER TABLE usuarios ADD COLUMN condiciones TEXT DEFAULT ''"))
                    conn.commit()
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
