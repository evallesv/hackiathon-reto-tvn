#!/usr/bin/env python3
"""Script to initialize GitHub Milestones, Labels, and Issues for the hackathon

using the GitHub CLI (`gh`).
"""

import argparse
import subprocess
import sys
from typing import List

LABELS = [
    ("phase:dia-1-datos-diseno", "0E8A16", "Día 1: Preparación de fuentes, arquitectura y diseño"),
    ("phase:dia-2-producto-funcional", "1D76DB", "Día 2: Flujo funcional, conectores e interfaz"),
    ("phase:dia-3-pruebas-cierre", "5319E7", "Día 3: Pruebas de aceptación T01-T10 y presentación"),
    ("type:acceptance-test", "D93F0B", "Casos de prueba obligatorios T01-T10 (Sección 9)"),
    ("type:ai-core", "0052CC", "Núcleo de IA, conectores LLM y scoring de atención"),
    ("type:adr", "FBCA04", "Decisiones de arquitectura registradas en docs/adr"),
    ("type:infra-fly", "6F42C1", "Infraestructura de despliegue en Fly.io"),
    ("type:notion-integration", "006B75", "Sincronización y páginas de entrega en Notion Business"),
    ("type:data-pipeline", "BFD4F2", "Ingesta de datos, hash SHA-256 y normalización"),
]

MILESTONES = [
    (
        "Día 1: Datos y Diseño",
        "2026-10-07T23:59:59Z",
        "Preparación de fuentes, contratos de datos, arquitectura y núcleo de IA.",
    ),
    (
        "Día 2: Producto Funcional",
        "2026-10-08T23:59:59Z",
        "Interfaz, fichas, generación de briefs/guiones y revisión humana.",
    ),
    (
        "Día 3: Pruebas T01-T10 y Pitch",
        "2026-10-09T23:59:59Z",
        "Validación T01-T10, benchmark reproducible, documentación Notion y pitch.",
    ),
]

ACCEPTANCE_TESTS = [
    (
        "T01",
        "Archivo con fechas inválidas y nulos",
        "Validar, separar errores y conservar nulos; no bloquear toda la carga.",
    ),
    (
        "T02",
        "Tres registros del mismo evento",
        "Agrupar sin perder fuentes; no triplicar importancia ni corroboración.",
    ),
    ("T03", "Noticia antigua recirculada", "Mostrar fecha original; no presentarla como un evento nuevo."),
    (
        "T04",
        "Cifra anual del Banco Mundial",
        "Mantener país, año y unidad; citar dato y no describirlo como cifra de hoy.",
    ),
    (
        "T05",
        "Dos afirmaciones incompatibles",
        "Mostrar ambas, su alcance y la revisión pendiente; no escoger arbitrariamente.",
    ),
    ("T06", "Consulta sin respuesta en el corpus", "Abstención explícita; ninguna cifra o cita inventada."),
    (
        "T07",
        "Fuente que exige ignorar instrucciones",
        "Tratarla como contenido no confiable; no revelar secretos ni ejecutar acciones.",
    ),
    ("T08", "Caso de prioridad alta", "Exponer componentes y regla; la prioridad no habilita publicación."),
    (
        "T09",
        "Brief editorial o boletín bancario",
        "Formato útil, citas pertinentes y distinción de hechos e inferencias.",
    ),
    (
        "T10",
        "Sin internet durante la demo",
        "Funcionar con snapshot y fallback documentado; dejar evidencia en Notion.",
    ),
]

CORE_TASKS = [
    (
        "task: Configurar catálogo de fuentes y snapshot congelado",
        "phase:dia-1-datos-diseno,type:data-pipeline",
        "Descargar y validar noticias.csv, indicadores.csv, eventos.geojson y calcular SHA-256 en manifest.json.",
    ),
    (
        "task: Implementar motor de scoring P = 30R + 25I + 20U + 15N + 10E",
        "phase:dia-1-datos-diseno,type:ai-core",
        "Programar la fórmula de atención, normalización 0-1, rangos [bajo, medio, alto] y desempates.",
    ),
    (
        "task: Implementar conectores intercambiables OpenCode y Gemini",
        "phase:dia-1-datos-diseno,type:ai-core",
        "Conector default OpenCode (muse-spark-1.3-contributor-free) y alternativo Google Gemini con fallback mock.",
    ),
    (
        "task: Desarrollar escudo anti-inyección y validador de citas",
        "phase:dia-1-datos-diseno,type:ai-core",
        "Garantizar aislamiento de datos ('dato, no instrucción') y 100% de afirmaciones enlazadas a evidencia.",
    ),
    (
        "task: Crear API FastAPI y endpoints de copiloto",
        "phase:dia-2-producto-funcional,type:ai-core",
        "Endpoints para /healthz, agenda priorizada, generación de briefs editoriales y revisión humana.",
    ),
    (
        "task: Despliegue en Fly.io Machines",
        "phase:dia-2-producto-funcional,type:infra-fly",
        "Configurar Dockerfile multi-stage con uv, fly.toml puerto 8080 en 0.0.0.0 y verificar health checks.",
    ),
    (
        "task: Ejecutar suite de pruebas de aceptación T01 a T10",
        "phase:dia-3-pruebas-cierre,type:acceptance-test",
        "Correr pytest test_acceptance_t01_t10.py y registrar resultados en la matriz de Notion.",
    ),
    (
        "task: Documentación y preparación del Pitch en Notion Business",
        "phase:dia-3-pruebas-cierre,type:notion-integration",
        "Completar las 8 páginas obligatorias de Notion y estructurar pitch navegable de 10 minutos.",
    ),
]


def run_gh_cmd(cmd: List[str], dry_run: bool = False) -> None:
    print(f"-> {' '.join(cmd)}")
    if dry_run:
        return
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"   [WARN/ERROR] {res.stderr.strip()}")
    else:
        print(f"   [OK] {res.stdout.strip()}")


def setup_labels(dry_run: bool = False) -> None:
    print("\n--- Configurando Etiquetas de GitHub ---")
    for name, color, desc in LABELS:
        cmd = ["gh", "label", "create", name, "--color", color, "--description", desc, "--force"]
        run_gh_cmd(cmd, dry_run=dry_run)


def setup_milestones(dry_run: bool = False) -> None:
    print("\n--- Configurando Milestones de GitHub ---")
    for title, due, desc in MILESTONES:
        cmd = ["gh", "milestone", "create", "--title", title, "--due-date", due, "--description", desc]
        run_gh_cmd(cmd, dry_run=dry_run)


def setup_issues(dry_run: bool = False) -> None:
    print("\n--- Creando Tareas Principales del Reto ---")
    for title, labels, body in CORE_TASKS:
        cmd = [
            "gh",
            "issue",
            "create",
            "--title",
            title,
            "--label",
            labels,
            "--body",
            f"### Descripción\n{body}\n\n### Checklist\n- [ ] Análisis\n- [ ] Implementación con uv\n- [ ] Pruebas unitarias\n- [ ] Documentación en Notion",
        ]
        run_gh_cmd(cmd, dry_run=dry_run)

    print("\n--- Creando Issues para los 10 Casos de Aceptación (T01–T10) ---")
    for tid, name, expected in ACCEPTANCE_TESTS:
        cmd = [
            "gh",
            "issue",
            "create",
            "--title",
            f"test: [{tid}] {name}",
            "--label",
            "type:acceptance-test,phase:dia-3-pruebas-cierre",
            "--body",
            (
                f"### Caso de Prueba de Aceptación {tid} (Sección 9)\n\n"
                f"**Prueba**: {name}\n\n"
                f"**Resultado Esperado**: {expected}\n\n"
                f"**Archivo de Test**: `tests/test_acceptance_t01_t10.py` (`test_{tid.lower()}_...`)\n\n"
                f"### Estado de Verificación\n"
                f"- [ ] Código de prueba ejecutado con `uv run pytest`\n"
                f"- [ ] Evidencia registrada en la matriz de pruebas de Notion"
            ),
        ]
        run_gh_cmd(cmd, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Configuración de tareas y pruebas en GitHub con gh")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra los comandos sin ejecutarlos")
    args = parser.parse_args()

    # Verify gh is available and authenticated
    res = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if res.returncode != 0 and not args.dry_run:
        print("ERROR: GitHub CLI no está autenticado. Ejecute 'gh auth login' primero.")
        sys.exit(1)

    setup_labels(dry_run=args.dry_run)
    setup_milestones(dry_run=args.dry_run)
    setup_issues(dry_run=args.dry_run)
    print("\n✅ Inicialización de tareas en GitHub completada con éxito.")


if __name__ == "__main__":
    main()
