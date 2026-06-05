import json
from sqlalchemy.orm import Session
from .models import Candidate, JobProfile


# ─── Candidates ───────────────────────────────────────────────

def candidate_exists(db: Session, cv_hash: str) -> bool:
    """Verifica si ya existe un CV con este hash (deduplicación)."""
    return db.query(Candidate).filter(Candidate.cv_hash == cv_hash).first() is not None


def create_candidate(db: Session, data: dict) -> Candidate:
    """Crea un nuevo candidato a partir del estado final del grafo."""
    tecnologias = data.get("tecnologias", [])
    candidate = Candidate(
        cv_hash=data["cv_hash"],
        client_id=data["client_id"],
        nombre=data.get("nombre"),
        email=data.get("email"),
        telefono=data.get("telefono"),
        anios_experiencia=data.get("anios_experiencia"),
        tecnologias=json.dumps(tecnologias) if isinstance(tecnologias, list) else tecnologias,
        ultimo_cargo=data.get("ultimo_cargo"),
        nivel_ingles=data.get("nivel_ingles"),
        rag_score=data.get("rag_score"),
        score_draft=data.get("score_draft"),
        score_final=data.get("score_final"),
        score_reasoning=data.get("score_reasoning"),
        correction_notes=data.get("correction_notes"),
        decision=data.get("decision"),
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def get_talent_bank(db: Session, client_id: str) -> list[Candidate]:
    """Devuelve todos los candidatos en el banco de talentos de un cliente."""
    return (
        db.query(Candidate)
        .filter(Candidate.client_id == client_id, Candidate.decision == "talent_bank")
        .order_by(Candidate.score_final.desc())
        .all()
    )


# ─── Job Profiles ─────────────────────────────────────────────

def create_job_profile(db: Session, client_id: str, position_name: str,
                       profile_text: str, chroma_collection: str) -> JobProfile:
    profile = JobProfile(
        client_id=client_id,
        position_name=position_name,
        profile_text=profile_text,
        chroma_collection=chroma_collection,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_job_profiles(db: Session, client_id: str) -> list[JobProfile]:
    return db.query(JobProfile).filter(JobProfile.client_id == client_id).all()