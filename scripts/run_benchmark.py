#!/usr/bin/env python3
"""Runner for the development benchmark and its explicitly scoped comparisons."""

import argparse
import asyncio
import json
from pathlib import Path

from hackiathon_reto_tvn.config import get_settings
from hackiathon_reto_tvn.services.baseline_evaluator import BaselineEvaluator
from hackiathon_reto_tvn.services.copilot_service import CopilotService


async def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Ejecuta el benchmark de desarrollo o un holdout externo custodiado.")
    parser.add_argument("--jury-file", type=Path, help="Archivo JSONL externo con filas reservado_jurado.")
    parser.add_argument("--output", type=Path, help="Ruta externa para guardar el reporte del holdout.")
    args = parser.parse_args()

    project_root = settings.DATA_DIR.resolve().parent
    only_dev = args.jury_file is None
    if only_dev and args.output is not None:
        parser.error("--output solo se usa junto con --jury-file.")
    if not only_dev:
        if args.output is None:
            parser.error("--jury-file requiere --output para mantener el reporte fuera del proyecto.")
        jury_path = args.jury_file.resolve()
        output_path = args.output.resolve()
        if jury_path.is_relative_to(project_root):
            parser.error("El archivo del jurado debe estar fuera del repositorio y bajo custodia independiente.")
        if output_path.is_relative_to(project_root):
            parser.error("El reporte del jurado debe guardarse fuera del repositorio.")
        if jury_path == output_path:
            parser.error("El archivo de salida debe ser distinto del archivo de entrada.")
    else:
        jury_path = None
        output_path = settings.DATA_DIR / "benchmark_results.json"

    print("=" * 75)
    print("  HACKIATHON 4TA EDICIÓN — TVN MEDIA COPILOT BENCHMARK SUITE")
    print(f"  Entorno: {settings.ENVIRONMENT} | LLM: {settings.LLM_PROVIDER} | Decision: {settings.DECISION_PROVIDER}")
    print("=" * 75)

    service = CopilotService(settings=settings)
    evaluator = BaselineEvaluator(service=service, settings=settings)

    if only_dev:
        print("\n[1/3] Ejecutando únicamente las consultas de desarrollo (40)...")
        results = await evaluator.run_benchmark_suite(only_dev=True)
    else:
        print("\n[1/3] Ejecutando holdout externo custodiado...")
        results = await evaluator.run_benchmark_suite(benchmark_path=jury_path, only_dev=False)

    if "error" in results:
        raise RuntimeError(results["error"])

    summary = results["resumen_benchmark"]
    baselines = results["comparativa_baselines"]

    print("\n" + "-" * 75)
    print("  RESUMEN DE MÉTRICAS OBLIGATORIAS (SECCIÓN 9.1 DEL RETO)")
    print("-" * 75)
    print(f"  • Total consultas evaluadas:        {summary['total_consultas_ejecutadas']}")
    citation_rate = summary["respuestas_sustentadas_con_ids_validos_porcentaje"]
    answer_rate = summary["respuestas_correctas_con_fuente_esperada_porcentaje"]
    abstention_rate = summary["tasa_abstencion_porcentaje"]
    adversarial_rate = summary["resistencia_adversarial_porcentaje"]
    if citation_rate is None:
        print("  • Respuestas con IDs de cita válidos: N/D (sin consultas sustentadas)")
    else:
        print(
            "  • Respuestas con IDs de cita válidos: "
            f"{citation_rate}%  ({summary['respuestas_sustentadas_con_ids_validos']}/"
            f"{summary['consultas_sustentadas_evaluadas']}; meta: {summary['meta_ids_cita_validos']})"
        )
    if answer_rate is None:
        print("  • Valor + fuente esperados:          N/D (sin consultas sustentadas)")
    else:
        print(
            "  • Valor + fuente esperados:          "
            f"{answer_rate}%  ({summary['respuestas_correctas_con_fuente_esperada']}/"
            f"{summary['consultas_sustentadas_evaluadas']}; coincidencia literal)"
        )
    abstention_text = f"{abstention_rate}%" if abstention_rate is not None else "N/D (sin consultas sin respuesta)"
    adversarial_text = f"{adversarial_rate}%" if adversarial_rate is not None else "N/D (sin consultas adversariales)"
    print(f"  • Tasa de abstención explícita:     {abstention_text}")
    print(
        f"  • Abstenciones correctas:          {summary['abstenciones_correctas']}/"
        f"{summary['consultas_sin_respuesta_evaluadas']}"
    )
    print(
        f"  • Falsas abstenciones:             {summary['abstenciones_incorrectas']}/"
        f"{summary['consultas_sustentadas_evaluadas']} respondibles"
    )
    print(f"  • Resistencia adversarial (T07):    {adversarial_text}")
    print(f"  • Latencia mediana (p50):           {summary['latencia_mediana_ms']} ms")
    print(f"  • Latencia percentil 95 (p95):      {summary['latencia_p95_ms']} ms")
    print("  • Tokens y costo:                  no medidos")

    print("\n" + "-" * 75)
    if only_dev:
        print("  COMPARATIVA CONTRA BASELINES SIMPLES (SECCIÓN 8 DEL RETO)")
    else:
        print("  SIN COMPARATIVAS DE DESARROLLO EN EL REPORTE DEL JURADO")
    print("-" * 75)
    if only_dev:
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
            f"    - Proveedor efectivo ({model['provider']}/{model['model']}): "
            f"Macro-F1={model['f1']} | Prec={model['precision']} | Rec={model['recall']}"
        )
        print(
            f"    - Configurado: {model['provider_configurado']}/{model['model_configurado']}; "
            f"fallbacks: {model['ejecuciones_fallback']}/{model['muestra']}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResultados exportados exitosamente a {output_path}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
