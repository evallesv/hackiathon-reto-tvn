#!/usr/bin/env python3
"""Runner for the development benchmark and its explicitly scoped comparisons."""

import asyncio
import json
from pathlib import Path

from hackiathon_reto_tvn.config import get_settings
from hackiathon_reto_tvn.services.baseline_evaluator import BaselineEvaluator
from hackiathon_reto_tvn.services.copilot_service import CopilotService


async def main() -> None:
    settings = get_settings()
    print("=" * 75)
    print("  HACKIATHON 4TA EDICIÓN — TVN MEDIA COPILOT BENCHMARK SUITE")
    print(f"  Entorno: {settings.ENVIRONMENT} | LLM: {settings.LLM_PROVIDER} | Decision: {settings.DECISION_PROVIDER}")
    print("=" * 75)

    service = CopilotService(settings=settings)
    evaluator = BaselineEvaluator(service=service, settings=settings)

    print("\n[1/3] Ejecutando únicamente las consultas de desarrollo (40)...")
    results = await evaluator.run_benchmark_suite(only_dev=True)

    if "error" in results:
        raise RuntimeError(results["error"])

    summary = results["resumen_benchmark"]
    baselines = results["comparativa_baselines"]

    print("\n" + "-" * 75)
    print("  RESUMEN DE MÉTRICAS OBLIGATORIAS (SECCIÓN 9.1 DEL RETO)")
    print("-" * 75)
    print(f"  • Total consultas evaluadas:        {summary['total_consultas_ejecutadas']}")
    print(
        "  • Respuestas con IDs de cita válidos: "
        f"{summary['respuestas_sustentadas_con_ids_validos_porcentaje']}%  "
        f"({summary['respuestas_sustentadas_con_ids_validos']}/{summary['consultas_sustentadas_evaluadas']}; "
        f"meta: {summary['meta_ids_cita_validos']})"
    )
    print(
        f"  • Tasa de abstención explícita:     {summary['tasa_abstencion_porcentaje']}%  (Meta: {summary['meta_tasa_abstencion']})"
    )
    print(f"  • Resistencia adversarial (T07):    {summary['resistencia_adversarial_porcentaje']}%")
    print(f"  • Latencia mediana (p50):           {summary['latencia_mediana_ms']} ms")
    print(f"  • Latencia percentil 95 (p95):      {summary['latencia_p95_ms']} ms")

    print("\n" + "-" * 75)
    print("  COMPARATIVA CONTRA BASELINES SIMPLES (SECCIÓN 8 DEL RETO)")
    print("-" * 75)
    rank = baselines["ranking_priorizacion"]
    print(f"  [Tarea A] {rank['tarea']} ({rank['metrica']}):")
    print(f"    - Baseline (Recencia por fecha):  {rank['baseline_recencia']['precision_at_5']}")
    print(f"    - Copilot (Atención P):           {rank['copilot_score_p']['precision_at_5']}")
    relative_gain = rank["mejora_relativa_porcentaje"]
    if relative_gain is None:
        print("    - Mejora relativa observada:      No calculable (baseline P@5 = 0)")
    else:
        print(f"    - Mejora relativa observada:      {relative_gain:+.1f}%")

    cla = baselines["clasificacion_contradicciones"]
    print(f"\n  [Tarea B] {cla['tarea']} ({cla['metrica']}):")
    print(
        f"    - Baseline (Regex/Palabras clave): F1={cla['baseline_regex']['f1']} | Prec={cla['baseline_regex']['precision']} | Rec={cla['baseline_regex']['recall']}"
    )
    model = cla["modelo_decision"]
    print(
        f"    - Adaptador configurado ({model['provider']}/{model['model']}): "
        f"Macro-F1={model['f1']} | Prec={model['precision']} | Rec={model['recall']}"
    )

    # Save to data/benchmark_results.json
    out_path = Path("data/benchmark_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResultados exportados exitosamente a {out_path}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
