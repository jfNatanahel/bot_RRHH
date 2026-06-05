import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import settings


class Base(DeclarativeBase):
    pass


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cv_hash = Column(String, unique=True, nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)

    # Datos extraídos por el Agente 1
    nombre = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    anios_experiencia = Column(Integer, nullable=True)
    tecnologias = Column(Text, nullable=True)          # JSON serializado
    ultimo_cargo = Column(String, nullable=True)
    nivel_ingles = Column(String, nullable=True)

    # Scoring
    rag_score = Column(Float, nullable=True)
    score_draft = Column(Integer, nullable=True)
    score_final = Column(Integer, nullable=True)
    score_reasoning = Column(Text, nullable=True)
    correction_notes = Column(Text, nullable=True)

    # Decisión
    decision = Column(String, nullable=True)           # "approved" | "talent_bank"

    created_at = Column(DateTime, default=datetime.utcnow)


class JobProfile(Base):
    __tablename__ = "job_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, nullable=False, index=True)
    position_name = Column(String, nullable=False)
    profile_text = Column(Text, nullable=False)
    chroma_collection = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Engine y sesión
def get_engine():
    db_path = settings.database_url
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db():
    """Crea las tablas si no existen. Llamar al arrancar la app."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_session():
    """Context manager de sesión para usar con 'with'."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()