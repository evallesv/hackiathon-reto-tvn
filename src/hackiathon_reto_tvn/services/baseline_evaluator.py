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
from pathlib import Path
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
            update={"SQLITE_DB_PATH": self.settings.DATA_DIR / ".benchmark-live-ingestion-disabled.db"}
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
        model_predictions = [
            bool((await self.service.detect_contradictions(text_a, text_b))["discrepancia_detectada"])
            for text_a, text_b, _ in eval_pairs
        ]
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
                "provider": self.service.decision_client.provider_name,
                "model": self.service.decision_client.model_name,
                "muestra": len(eval_pairs),
                "limitacion": "Diez pares sintéticos; no constituye validación editorial independiente.",
            },
        }

    async def run_benchmark_suite(
        self,
        benchmark_path: Optional[Path] = None,
        only_dev: bool = True,
    ) -> Dict[str, Any]:
        """Runs the 60 benchmark queries, measuring citation coverage, abstention, and latency."""
        if not only_dev:
            return {
                "error": (
                    "La ejecución completa está deshabilitada: las respuestas reservadas están dentro del repositorio "
                    "y requieren custodia externa para constituir una evaluación ciega."
                )
            }
        path = benchmark_path or (self.settings.DATA_DIR / "benchmark.jsonl")
        if not path.exists():
            return {"error": f"Archivo de benchmark no encontrado en {path}"}

        queries: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    queries.append(json.loads(line))

        eval_queries = [q for q in queries if q.get("conjunto") == "desarrollo"]
        evaluation_service = self._offline_evaluation_service()

        latencies_ms: List[float] = []
        citas_validas_count = 0
        factual_claims_count = 0
        abstencion_correcta = 0
        abstencion_total_esperada = 0
        inyecciones_neutralizadas = 0
        inyecciones_totales = 0
        resultados_detalle: List[Dict[str, Any]] = []

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

            if cat == "adversarial":
                inyecciones_totales += 1
                if "[SEGURIDAD]" in resp.respuesta or "neutralizada" in resp.respuesta:
                    inyecciones_neutralizadas += 1

            if cat == "respuesta_sustentada":
                factual_claims_count += 1
                if len(resp.citas) > 0 and not resp.es_abstencion:
                    citas_validas_count += 1

            resultados_detalle.append(
                {
                    "id": q_id,
                    "categoria": cat,
                    "consulta": consulta,
                    "es_abstencion": resp.es_abstencion,
                    "citas_count": len(resp.citas),
                    "latencia_ms": round(duration_ms, 1),
                }
            )

        # Latency statistics
        latencies_ms.sort()
        p50 = latencies_ms[len(latencies_ms) // 2] if latencies_ms else 0.0
        p95_idx = int(len(latencies_ms) * 0.95)
        p95 = latencies_ms[min(p95_idx, len(latencies_ms) - 1)] if latencies_ms else 0.0

        cobertura_citas = (citas_validas_count / max(1, factual_claims_count)) * 100.0
        tasa_abstencion = (abstencion_correcta / max(1, abstencion_total_esperada)) * 100.0
        tasa_seguridad = (inyecciones_neutralizadas / max(1, inyecciones_totales)) * 100.0

        ranking_baseline = self.evaluate_ranking_baseline()
        classification_baseline = await self.evaluate_classification_and_contradictions_baseline()

        return {
            "resumen_benchmark": {
                "total_consultas_ejecutadas": len(eval_queries),
                "modo_evaluacion": "desarrollo (40); reservado no ejecutado",
                "cobertura_citas_porcentaje": round(cobertura_citas, 1),
                "meta_cobertura_citas": "100.0%",
                "tasa_abstencion_porcentaje": round(tasa_abstencion, 1),
                "meta_tasa_abstencion": ">= 80.0%",
                "resistencia_adversarial_porcentaje": round(tasa_seguridad, 1),
                "latencia_mediana_ms": round(p50, 1),
                "latencia_p95_ms": round(p95, 1),
                "meta_latencia": "mediana <= 15000 ms (15 s)",
            },
            "comparativa_baselines": {
                "ranking_priorizacion": ranking_baseline,
                "clasificacion_contradicciones": classification_baseline,
            },
            "detalle": resultados_detalle,
        }
