from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

FASE4_DIR = Path(__file__).resolve().parent
if str(FASE4_DIR) not in sys.path:
    sys.path.insert(0, str(FASE4_DIR))

from request_log import FIELDS, _log_path  # noqa: E402


def analizar_registro(ruta_log: Path) -> dict[str, int | float | str]:
    """Lee el CSV de solicitudes y calcula total y porcentaje de errores 4xx/5xx."""
    if not ruta_log.exists() or ruta_log.stat().st_size == 0:
        return {
            "total": 0,
            "fallos": 0,
            "porcentaje_fallos": 0.0,
            "estado": "sin solicitudes",
        }

    with ruta_log.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        filas = [
            fila
            for fila in reader
            if fila and fila.get("estado_http") not in (None, "")
        ]

    total = len(filas)
    if total == 0:
        return {
            "total": 0,
            "fallos": 0,
            "porcentaje_fallos": 0.0,
            "estado": "sin solicitudes",
        }

    fallos = 0
    for fila in filas:
        codigo = int(float(fila["estado_http"]))
        if 400 <= codigo < 600:
            fallos += 1

    porcentaje = round((fallos / total) * 100, 1)
    return {
        "total": total,
        "fallos": fallos,
        "porcentaje_fallos": porcentaje,
        "estado": "ok",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula el total de solicitudes a /predict y el porcentaje de fallos 4xx/5xx."
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="Ruta opcional al archivo CSV de registro (por defecto usa PREDICTION_LOG_PATH o fase-4/logs/predicciones.csv).",
    )
    args = parser.parse_args()

    ruta_objetivo = _log_path(args.log)
    resumen = analizar_registro(ruta_objetivo)

    if resumen["total"] == 0:
        print("Total de solicitudes: 0")
        print("sin solicitudes")
    else:
        porcentaje_fmt = f"{resumen['porcentaje_fallos']:.1f}".replace(".", ",")
        print(f"Total de solicitudes: {resumen['total']}")
        print(f"Fallos HTTP 4xx/5xx: {resumen['fallos']} ({porcentaje_fmt} %)")


if __name__ == "__main__":
    main()
