import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rag.vector_store import cargar_job_profile
from config.clients import get_client
from database.models import init_db, SessionLocal
from database.crud import create_job_profile


def main():
    parser = argparse.ArgumentParser(description="Carga un job profile en Chroma y SQLite.")
    parser.add_argument("--client_id", required=True, help="ID del cliente (ej: demo)")
    parser.add_argument("--position", required=True, help="Nombre del puesto")
    parser.add_argument("--file", help="Ruta al archivo .txt con el perfil")
    parser.add_argument("--text", help="Texto del perfil directamente")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            profile_text = f.read()
    elif args.text:
        profile_text = args.text
    else:
        print("ERROR: Debés proveer --file o --text")
        sys.exit(1)

    client_config = get_client(args.client_id)
    collection_name = client_config["chroma_collection"]

    print(f"Cargando perfil '{args.position}' para cliente '{args.client_id}'...")
    print(f"Colección Chroma: {collection_name}")

    cargar_job_profile(
        collection_name=collection_name,
        profile_text=profile_text,
        metadata={"client_id": args.client_id, "position": args.position},
    )

    init_db()
    db = SessionLocal()
    create_job_profile(
        db=db,
        client_id=args.client_id,
        position_name=args.position,
        profile_text=profile_text,
        chroma_collection=collection_name,
    )
    db.close()

    print("✓ Perfil cargado exitosamente.")


if __name__ == "__main__":
    main()