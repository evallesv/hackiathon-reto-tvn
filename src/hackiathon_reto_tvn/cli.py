"""Command Line Interface (CLI) for HackIAthon Copilot."""

import argparse
import asyncio
import sys

from hackiathon_reto_tvn.config import get_settings
from hackiathon_reto_tvn.services.copilot_service import CopilotService


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hackiathon-tvn",
        description="Copiloto de inteligencia informativa para TVN Media",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Command: status
    subparsers.add_parser("status", help="Muestra el estado del sistema y configuración de LLM")

    # Command: agenda
    agenda_parser = subparsers.add_parser("agenda", help="Calcula la agenda priorizada (CU-01)")
    agenda_parser.add_argument("--top", type=int, default=5, help="Número de casos en el ranking")

    # Command: manifest
    subparsers.add_parser("manifest", help="Genera y valida manifest.json con SHA-256")

    # Command: draft
    subparsers.add_parser("draft", help="Genera borrador editorial para el caso top 1")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    settings = get_settings()
    service = CopilotService(settings=settings)

    if args.command == "status":
        print("=== Estado del Copiloto HackIAthon TVN ===")
        print(f"Ambiente:           {settings.ENVIRONMENT}")
        print(f"Modelo Decisión:    {service.decision_client.provider_name} ({service.decision_client.model_name})")
        print(f"Proveedor LLM:      {service.llm.provider_name} ({service.llm.model_name})")
        print(f"Datos Raw:          {settings.RAW_DATA_DIR}")
        print(f"Puerto API:         {settings.PORT}")

    elif args.command == "agenda":
        print(f"Calculando ranking priorizado (Top {args.top})...\n")
        agenda = service.prioritize_agenda(top_n=args.top)
        for idx, caso in enumerate(agenda, 1):
            print(f"[{idx}] {caso.id_caso} | Puntaje: {caso.puntaje}/100 | Evidencia: {caso.estado_evidencia.value}")
            print(f"    Fuentes: {', '.join(caso.ids_fuente)}")
            if caso.afirmaciones:
                print(f"    Titular: {caso.afirmaciones[0].texto}")
            print()

    elif args.command == "manifest":
        print("Generando manifest.json con hashes SHA-256...")
        manifest = service.repo.generate_manifest(settings.DATA_DIR)
        print(f"Versión: {manifest.version} | Archivos procesados: {len(manifest.archivos)}")
        for item in manifest.archivos:
            print(f"  - {item.archivo}: {item.cantidad_registros} registros | SHA256: {item.sha256[:12]}...")

    elif args.command == "draft":

        async def _run_draft():
            agenda = service.prioritize_agenda(top_n=1)
            if not agenda:
                print("No se encontraron casos disponibles para redactar borrador.")
                return
            top_caso = agenda[0]
            print(f"Generando borrador editorial para {top_caso.id_caso} usando {service.llm.provider_name}...")
            borrador = await service.generate_tvn_editorial_package(top_caso)
            print("\n--- BORRADOR EDITORIAL GENERADO ---")
            print(f"Título: {borrador.titulo_propuesto}")
            print(f"\nBrief (<= 250 palabras):\n{borrador.brief_250}")
            print("\nPreguntas de investigación:")
            for q in borrador.preguntas_investigacion:
                print(f"  * {q}")
            print(f"\nGuion (45-60 seg):\n{borrador.guion_45_60s}")
            print(f"\nCopy Digital (<= 80 palabras):\n{borrador.copy_digital_80}")

        asyncio.run(_run_draft())


if __name__ == "__main__":
    main()
