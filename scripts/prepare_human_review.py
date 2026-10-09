"""Export a development report and its original corpus records for human support review."""

import argparse
import csv
import json
from pathlib import Path

from hackiathon_reto_tvn.config import Settings
from hackiathon_reto_tvn.services.copilot_service import CopilotService
from hackiathon_reto_tvn.services.human_review import prepare_review_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara revisión humana del sustento en desarrollo, sin emitir veredictos."
    )
    parser.add_argument("--report", type=Path, default=Path("data/benchmark_results.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/validation/revision_sustento.csv"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("La salida ya existe; usa una ruta nueva para preservar las revisiones anteriores.")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    settings = Settings(
        _env_file=None, ENVIRONMENT="test", LLM_PROVIDER="mock", DECISION_PROVIDER="mock", INGESTION_ENABLED=False
    )
    service = CopilotService(settings=settings)
    records = {news.id_noticia: news.model_dump() for news in service.load_query_news()}
    records.update(
        {
            f"{item.pais_iso3}-{item.indicador_id}-{item.anio}": item.model_dump()
            for item in service.load_query_indicators()
            if item.pais_iso3 and item.indicador_id and item.anio is not None
        }
    )
    records.update({event.id: event.model_dump() for event in service.load_query_events()})
    rows = prepare_review_rows(report, records)
    if not rows:
        parser.error("El reporte no contiene respuestas sustentadas emitidas para revisar.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Planilla: {args.output}. Unidades de respuesta: {len(rows)}. Sin veredictos ni afirmaciones adjudicadas.")


if __name__ == "__main__":
    main()
