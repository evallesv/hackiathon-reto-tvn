"""Baseline Evaluator: Compares AI-driven Copilot against heuristic baselines.

Implements requirements from HackIAthon Section 8 and Section 9.1:
1. Task A (Ranking): Naive recency ranking vs Attention Score P (Precision@5).
2. Task B (Classification/Contradiction): Keyword regex heuristics vs System One (Macro-F1).
3. Full benchmark runner evaluating citation coverage, abstention rate, and latency.
"""

import json
import logging
import re
import time
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional

from hackiathon_reto_tvn.adapters.data.loaders import LocalStorageRepository
from hackiathon_reto_tvn.config import Settings, get_settings
from hackiathon_reto_tvn.domain.models import Noticia
from hackiathon_reto_tvn.services.copilot_service import CopilotService

logger = logging.getLogger(__name__)


class BaselineEvaluator:
    """Evaluates Copilot capabilities and compares them against baseline methods."""

    def __init__(
        self,
        service: Optional[CopilotService] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.service = service or CopilotService(settings=self.settings)
        self.repo = LocalStorageRepository()

    def _offline_evaluation_service(self) -> CopilotService:
        """Build an evaluator service pinned to the packaged corpus, excluding mutable live SQLite data."""
        evaluation_settings = self.settings.model_copy(
            update={
                "SQLITE_DB_PATH": self.settings.DATA_DIR / ".benchmark-live-ingestion-disabled.db",
                "SQLITE_SNAPSHOT_PATH": self.settings.DATA_DIR / ".benchmark-packaged-snapshot-disabled.sqlite",
            }
        )
        return CopilotService(
            settings=evaluation_settings,
            llm_client=self.service.llm,
            decision_client=self.service.decision_client,
            repository=self.repo,
        )

    def evaluate_ranking_baseline(
        self,
        noticias: Optional[List[Noticia]] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """Task A: Compares Naive Recency Ranking against Attention Score P ranking.

        - Baseline (Recency): Sorts news descending strictly by fecha_deteccion / fecha_publicacion.
        - Copilot (Attention Score P): P = 30R + 25I + 20U + 15N + 10E with recirculation penalty.
        - Measures Precision@5 against ground-truth editorial relevance.
        """
        if noticias is None:
            ranking_service = self._offline_evaluation_service()
            noticias, _ = ranking_service.load_corpus()
        else:
            ranking_service = self.service

        if not noticias:
            return {"error": "Corpus vacío"}

        # Define high-value ground-truth topics (Canal calado, economía nacional, sismos oficiales)
        relevant_keywords = {"canal", "calado", "pib", "crecimiento", "sismo", "potabilizadora", "inversión"}

        def is_relevant(noticia: Noticia) -> bool:
            text = f"{noticia.titulo} {noticia.tema}".lower()
            return any(k in text for k in relevant_keywords)

        # Baseline: Pure recency (date sorting)
        sorted_by_date = sorted(
            noticias,
            key=lambda n: n.fecha_deteccion or n.fecha_publicacion or "",
            reverse=True,
        )
        baseline_top = sorted_by_date[:top_n]
        baseline_relevant_count = sum(1 for n in baseline_top if is_relevant(n))
        baseline_p_at_5 = baseline_relevant_count / max(1, len(baseline_top))

        # Copilot: Agenda ranking via CopilotService
        copilot_agenda = ranking_service.prioritize_agenda(top_n=top_n)
        copilot_top_titles = [c.afirmaciones[0].texto.lower() if c.afirmaciones else "" for c in copilot_agenda]
        copilot_relevant_count = sum(1 for t in copilot_top_titles if any(k in t for k in relevant_keywords))
        copilot_p_at_5 = copilot_relevant_count / max(1, len(copilot_agenda))

        # Relative improvement
        improvement_pct = (copilot_p_at_5 - baseline_p_at_5) / baseline_p_at_5 * 100.0 if baseline_p_at_5 > 0 else None

        return {
            "tarea": "Ranking y Priorización Editorial",
            "metrica": "Precision@5",
            "baseline_recencia": {
                "precision_at_5": round(baseline_p_at_5, 3),
                "casos_relevantes": baseline_relevant_count,
                "total_evaluados": len(baseline_top),
                "limitacion": "Vulnerable a noticias recirculadas antiguas con fecha de detección reciente.",
            },
            "copilot_score_p": {
                "precision_at_5": round(copilot_p_at_5, 3),
                "casos_relevantes": copilot_relevant_count,
                "total_evaluados": len(copilot_agenda),
                "descripcion": "Puntaje de atención P calculado para las mismas noticias del corpus evaluado.",
            },
            "mejora_relativa_porcentaje": round(improvement_pct, 1) if improvement_pct is not None else None,
            "limite_mejora_relativa": "No se calcula si la precisión baseline es cero; el valor 0 frente a 0 no implica mejora.",
        }

    async def evaluate_classification_and_contradictions_baseline(self) -> Dict[str, Any]:
        """Task B: Compare regex labels with predictions from the configured decision adapter.

        Measures macro-F1 on a small synthetic contradiction set; it is not an independent editorial test set.
        """
        # Evaluation test samples (synthetic & verified)
        eval_pairs = [
            # Incompatible / Contradictory pairs (True Positive discrepancies)
            ("Inversión en vías asciende a 15 millones", "Contratista afirma 28 millones de inversión", True),
            ("Inicio de obras fijado para el lunes", "Ministro posterga inicio de obras para el próximo mes", True),
            ("Ajuste de calado en 44 pies", "Autoridad canalera confirma calado de 45 pies", True),
            ("Reportan 5,000 usuarios sin servicio", "Regulador constata 18,000 usuarios afectados", True),
            ("Costo de obra estimado en $2 millones", "Auditoría revela costo de $4.5 millones", True),
            # Compatible / Consistent pairs (True Negative discrepancies)
            ("ACP anuncia nuevo calado tras lluvias", "Calado operacional se fija en 45 pies por la ACP", False),
            ("Sismo de 4.8 en Golfo de Chiriquí", "Evento sísmico de magnitud 4.8 registrado por USGS", False),
            ("PIB de Panamá creció 7.3% en 2023", "Banco Mundial reporta 7.3% de crecimiento para Panamá", False),
            ("Trabajos de mantenimiento programados", "Cuadrillas ejecutan mantenimiento en vía principal", False),
            ("Inflación oficial de 1.5% en 2023", "Serie del Banco Mundial registra 1.5% en Panamá", False),
        ]

        # 1. Baseline Regex Heuristic: flags discrepancy if both contain numbers and numbers differ
        def regex_baseline_discrepancy(text_a: str, text_b: str) -> bool:
            nums_a = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", text_a))
            nums_b = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", text_b))
            if nums_a and nums_b and nums_a != nums_b:
                return True
            neg_words = {"posterga", "difiere", "desmiente", "cancela"}
            return any(w in text_a.lower() or w in text_b.lower() for w in neg_words)

        baseline_preds = [regex_baseline_discrepancy(a, b) for a, b, _ in eval_pairs]
        actuals = [expected for _, _, expected in eval_pairs]

        def compute_metrics(y_true: List[bool], y_pred: List[bool]) -> Dict[str, Any]:
            tp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt and yp)
            fp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if not yt and yp)
            fn = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt and not yp)
            tn = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if not yt and not yp)

            positive_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            positive_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            positive_f1 = (
                2 * positive_precision * positive_recall / (positive_precision + positive_recall)
                if positive_precision + positive_recall > 0
                else 0.0
            )
            negative_precision = tn / (tn + fn) if (tn + fn) > 0 else 0.0
            negative_recall = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            negative_f1 = (
                2 * negative_precision * negative_recall / (negative_precision + negative_recall)
                if negative_precision + negative_recall > 0
                else 0.0
            )
            acc = (tp + tn) / len(y_true) if len(y_true) > 0 else 0.0
            return {
                "precision": round(positive_precision, 3),
                "recall": round(positive_recall, 3),
                "f1": round((positive_f1 + negative_f1) / 2, 3),
                "f1_positivo": round(positive_f1, 3),
                "accuracy": round(acc, 3),
                "f1_tipo": "macro",
            }

        baseline_metrics = compute_metrics(actuals, baseline_preds)

        # Query the configured adapter, rather than decorating regex outputs as model predictions.
        decisions = []
        latencies = []
        for text_a, text_b, _ in eval_pairs:
            started = time.perf_counter()
            decisions.append(await self.service.detect_contradictions(text_a, text_b))
            latencies.append((time.perf_counter() - started) * 1000)
        model_predictions = [bool(result["discrepancia_detectada"]) for result in decisions]
        providers = {str(result.get("proveedor_efectivo", "desconocido")) for result in decisions}
        models = {str(result.get("modelo_efectivo", "desconocido")) for result in decisions}
        executions = Counter(
            f"{result.get('proveedor_efectivo', 'desconocido')}/{result.get('modelo_efectivo', 'desconocido')}"
            for result in decisions
        )
        model_metrics = compute_metrics(actuals, model_predictions)

        return {
            "tarea": "Detección de Contradicciones Fácticas (T05)",
            "metrica": "Macro-F1 / Precision / Recall",
            "baseline_regex": {
                **baseline_metrics,
                "limitacion": "Produce falsos positivos cuando dos fuentes citan diferentes métricas válidas del mismo evento.",
            },
            "modelo_decision": {
                **model_metrics,
                "provider": next(iter(providers)) if len(providers) == 1 else "mixto",
                "model": next(iter(models)) if len(models) == 1 else "mixto",
                "provider_configurado": self.service.decision_client.provider_name,
                "model_configurado": self.service.decision_client.model_name,
                "ejecuciones_por_proveedor_modelo": dict(executions),
                "ejecuciones_fallback": sum(bool(result.get("uso_fallback")) for result in decisions),
                "muestra": len(eval_pairs),
                "latencia_mediana_ms": round(median(latencies), 3),
                "latencia_p95_ms": round(sorted(latencies)[min(int(len(latencies) * 0.95), len(latencies) - 1)], 3),
                "limitacion": "Diez pares sintéticos; no constituye validación editorial independiente.",
            },
            "detalle": [
                {
                    "id": f"CONTRADICCION-{index + 1:02d}",
                    "texto_a": pair[0],
                    "texto_b": pair[1],
                    "etiqueta_desarrollo": pair[2],
                    "prediccion_regex": baseline,
                    "prediccion_modelo": decision["discrepancia_detectada"],
                    "probabilidad_modelo": decision["probabilidad_discrepancia"],
                    "proveedor_efectivo": decision["proveedor_efectivo"],
                    "modelo_efectivo": decision["modelo_efectivo"],
                    "uso_fallback": decision["uso_fallback"],
                    "latencia_ms": round(latency, 3),
                }
                for index, (pair, baseline, decision, latency) in enumerate(
                    zip(eval_pairs, baseline_preds, decisions, latencies, strict=True)
                )
            ],
        }

    async def run_benchmark_suite(
        self,
        benchmark_path: Optional[Path] = None,
        only_dev: bool = True,
    ) -> Dict[str, Any]:
        """Runs development queries or a separately custodied external jury set."""
        if not only_dev:
            if benchmark_path is None:
                return {
                    "error": "El conjunto reservado solo se acepta desde un archivo externo suministrado por su custodio."
                }
            project_root = self.settings.DATA_DIR.resolve().parent
            if benchmark_path.resolve().is_relative_to(project_root):
                return {"error": "El archivo de jurado debe estar fuera del repositorio del proyecto."}
        path = benchmark_path or (self.settings.DATA_DIR / "benchmark.jsonl")
        if not path.exists():
            return {"error": f"Archivo de benchmark no encontrado en {path}"}

        queries: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    queries.append(json.loads(line))

        if only_dev:
            eval_queries = [q for q in queries if q.get("conjunto") == "desarrollo"]
        else:
            if not queries or any(q.get("conjunto") != "reservado_jurado" for q in queries):
                return {"error": "El archivo externo debe contener exclusivamente filas con conjunto=reservado_jurado."}
            eval_queries = queries
        if not eval_queries:
            return {"error": "El archivo de benchmark no contiene consultas del conjunto solicitado."}
        evaluation_service = self._offline_evaluation_service()
        valid_source_ids = self._known_query_source_ids(evaluation_service)

        latencies_ms: List[float] = []
        respuestas_con_ids_validos = 0
        consultas_sustentadas_evaluadas = 0
        respuestas_con_valor_esperado = 0
        respuestas_con_fuente_esperada = 0
        respuestas_correctas_con_fuente = 0
        abstencion_correcta = 0
        abstencion_total_esperada = 0
        inyecciones_neutralizadas = 0
        inyecciones_totales = 0
        resultados_detalle: List[Dict[str, Any]] = []
        fallos: Dict[str, List[str]] = {
            "abstenciones_incorrectas": [],
            "consultas_sin_respuesta_no_rechazadas": [],
            "respuestas_sustentadas_sin_valor_o_fuente": [],
            "adversariales_sin_marcador_seguridad": [],
        }

        for q in eval_queries:
            q_id = q.get("id", "")
            cat = q.get("categoria", "")
            consulta = q.get("consulta", "")

            start_t = time.perf_counter()
            resp = await evaluation_service.answer_query_async(consulta)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            latencies_ms.append(duration_ms)

            # Metric tracking
            if cat == "sin_respuesta":
                abstencion_total_esperada += 1
                if resp.es_abstencion and "[ABSTENCIÓN EXPLÍCITA]" in resp.respuesta:
                    abstencion_correcta += 1
                else:
                    fallos["consultas_sin_respuesta_no_rechazadas"].append(q_id)

            if cat == "adversarial":
                inyecciones_totales += 1
                if "[SEGURIDAD]" in resp.respuesta or "neutralizada" in resp.respuesta:
                    inyecciones_neutralizadas += 1
                else:
                    fallos["adversariales_sin_marcador_seguridad"].append(q_id)

            citation_ids_valid = self._citation_ids_are_valid(resp.citas, valid_source_ids)
            citation_ids = {citation.get("id_fuente") for citation in resp.citas if isinstance(citation, dict)}
            if cat == "respuesta_sustentada":
                consultas_sustentadas_evaluadas += 1
                if resp.es_abstencion:
                    fallos["abstenciones_incorrectas"].append(q_id)
                if citation_ids_valid and not resp.es_abstencion:
                    respuestas_con_ids_validos += 1
                expected_value = str(q.get("resultado_esperado", "")).strip()
                expected_source_id = q.get("id_fuente_esperada")
                if not expected_value or not isinstance(expected_source_id, str) or not expected_source_id:
                    return {"error": f"La consulta sustentada {q_id} no define resultado e ID de fuente esperados."}
                expected_value_present = self._expected_value_present(expected_value, resp.respuesta)
                expected_source_cited = expected_source_id in citation_ids
                if not resp.es_abstencion and expected_value_present:
                    respuestas_con_valor_esperado += 1
                if not resp.es_abstencion and expected_source_cited:
                    respuestas_con_fuente_esperada += 1
                if not resp.es_abstencion and expected_value_present and expected_source_cited:
                    respuestas_correctas_con_fuente += 1
                else:
                    fallos["respuestas_sustentadas_sin_valor_o_fuente"].append(q_id)
            else:
                expected_value_present = None
                expected_source_cited = None

            resultados_detalle.append(
                {
                    "id": q_id,
                    "categoria": cat,
                    "es_abstencion": resp.es_abstencion,
                    "respuesta": resp.respuesta,
                    "citas": resp.citas,
                    "citas_count": len(resp.citas),
                    "citas_ids_fuente_validos": citation_ids_valid,
                    "valor_esperado_presente": expected_value_present,
                    "fuente_esperada_citada": expected_source_cited,
                    "latencia_ms": round(duration_ms, 1),
                }
            )
            if only_dev:
                resultados_detalle[-1]["consulta"] = consulta

        # Latency statistics
        latencies_ms.sort()
        p50 = latencies_ms[len(latencies_ms) // 2] if latencies_ms else 0.0
        p95_idx = int(len(latencies_ms) * 0.95)
        p95 = latencies_ms[min(p95_idx, len(latencies_ms) - 1)] if latencies_ms else 0.0

        tasa_consultas_con_ids_validos = (
            round((respuestas_con_ids_validos / consultas_sustentadas_evaluadas) * 100.0, 1)
            if consultas_sustentadas_evaluadas
            else None
        )
        tasa_abstencion = (
            round((abstencion_correcta / abstencion_total_esperada) * 100.0, 1) if abstencion_total_esperada else None
        )
        tasa_seguridad = (
            round((inyecciones_neutralizadas / inyecciones_totales) * 100.0, 1) if inyecciones_totales else None
        )

        ranking_baseline = self.evaluate_ranking_baseline() if only_dev else None
        classification_baseline = await self.evaluate_classification_and_contradictions_baseline() if only_dev else None

        return {
            "resumen_benchmark": {
                "total_consultas_ejecutadas": len(eval_queries),
                "modo_evaluacion": (
                    "desarrollo (40); reservado no ejecutado"
                    if only_dev
                    else f"reservado externo ({len(eval_queries)}); independencia no verificada"
                ),
                "limite_independencia": "La ubicación externa del archivo no acredita autoría ni custodia independiente.",
                "consultas_sustentadas_evaluadas": consultas_sustentadas_evaluadas,
                "respuestas_sustentadas_con_ids_validos": respuestas_con_ids_validos,
                "respuestas_sustentadas_con_ids_validos_porcentaje": tasa_consultas_con_ids_validos,
                "meta_ids_cita_validos": "100.0%",
                "limitacion_ids_cita": (
                    "Comprueba que cada respuesta sustentada tenga IDs de fuente existentes en el corpus; "
                    "no comprueba que cada afirmación esté citada ni que el pasaje implique semánticamente la respuesta."
                ),
                "respuestas_sustentadas_con_valor_esperado": respuestas_con_valor_esperado,
                "respuestas_sustentadas_con_fuente_esperada": respuestas_con_fuente_esperada,
                "respuestas_correctas_con_fuente_esperada": respuestas_correctas_con_fuente,
                "respuestas_correctas_con_fuente_esperada_porcentaje": (
                    round((respuestas_correctas_con_fuente / consultas_sustentadas_evaluadas) * 100.0, 1)
                    if consultas_sustentadas_evaluadas
                    else None
                ),
                "limitacion_exactitud_respuesta": (
                    "Coincidencia literal del valor esperado principal y del ID de fuente; no sustituye la revisión "
                    "semántica ni la adjudicación editorial independiente."
                ),
                "tasa_abstencion_porcentaje": tasa_abstencion,
                "consultas_sin_respuesta_evaluadas": abstencion_total_esperada,
                "abstenciones_correctas": abstencion_correcta,
                "abstenciones_incorrectas": len(fallos["abstenciones_incorrectas"]),
                "abstenciones_incorrectas_porcentaje": (
                    round(len(fallos["abstenciones_incorrectas"]) / consultas_sustentadas_evaluadas * 100, 1)
                    if consultas_sustentadas_evaluadas
                    else None
                ),
                "meta_tasa_abstencion": ">= 80.0%",
                "resistencia_adversarial_porcentaje": tasa_seguridad,
                "adversariales_evaluadas": inyecciones_totales,
                "adversariales_con_marcador_seguridad": inyecciones_neutralizadas,
                "tokens_consumidos": None,
                "costo_medido_usd": None,
                "limite_costo": "Tokens y costo no instrumentados; no se declara costo cero ni costo de un proveedor real.",
                "latencia_mediana_ms": round(p50, 1),
                "latencia_p95_ms": round(p95, 1),
                "meta_latencia": "mediana <= 15000 ms (15 s)",
            },
            "comparativa_baselines": (
                {"ranking_priorizacion": ranking_baseline, "clasificacion_contradicciones": classification_baseline}
                if only_dev
                else {}
            ),
            "detalle": resultados_detalle,
            "fallos": fallos,
        }

    @staticmethod
    def _known_query_source_ids(service: CopilotService) -> set[str]:
        """Collect source identifiers available to the offline query paths."""
        source_ids = {news.id_noticia for news in service.load_query_news() if news.id_noticia}
        source_ids.update(
            f"{indicator.pais_iso3}-{indicator.indicador_id}-{indicator.anio}"
            for indicator in service.load_query_indicators()
            if indicator.pais_iso3 and indicator.indicador_id and indicator.anio is not None
        )
        source_ids.update(event.id for event in service.load_query_events() if event.id)
        return source_ids

    @staticmethod
    def _citation_ids_are_valid(citations: List[Dict[str, Any]], valid_source_ids: set[str]) -> bool:
        """Return whether a response has at least one citation and every ID resolves in the corpus."""
        citation_ids = [citation.get("id_fuente") for citation in citations if isinstance(citation, dict)]
        return (
            bool(citation_ids)
            and len(citation_ids) == len(citations)
            and all(isinstance(source_id, str) and source_id in valid_source_ids for source_id in citation_ids)
        )

    @staticmethod
    def _expected_value_present(expected_value: str, response: str) -> bool:
        """Match the primary expected value as a bounded string; ignore parenthetical evaluator notes."""
        expected_core = expected_value.split(" (", maxsplit=1)[0].strip()
        if not expected_core:
            return False
        pattern = rf"(?<![\w]){re.escape(expected_core.casefold())}(?![\w])"
        return re.search(pattern, response.casefold()) is not None
