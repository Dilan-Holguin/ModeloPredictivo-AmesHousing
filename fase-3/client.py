"""Cliente sencillo: envía una vivienda real de ejemplo a POST /predict.

Uso:
    python fase-3/client.py                      # fila 0 de ejemplo_prediccion.csv
    python fase-3/client.py --fila 1
    python fase-3/client.py --invalida           # quita OverallQual -> la API responde 422
    python fase-3/client.py --url http://localhost:8000
Solo usa la biblioteca estándar de Python.
"""

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

CSV_EJEMPLO = Path(__file__).resolve().parents[1] / "fase-2" / "data" / "ejemplo_prediccion.csv"
# Columnas que el modelo trata como numéricas (el resto es categórico).
sys.path.insert(0, str(CSV_EJEMPLO.parents[1]))
from src.config import FEATURE_COLUMNS, NUMERIC_COLUMNS  # noqa: E402

NULOS = {"", "NA", "nan", "NaN"}


def construir_payload(fila: int) -> dict:
    with CSV_EJEMPLO.open(encoding="utf-8", newline="") as stream:
        registro = list(csv.DictReader(stream))[fila]
    payload = {}
    for columna in FEATURE_COLUMNS:
        valor = registro[columna]
        if valor in NULOS:
            payload[columna] = None
        elif columna in NUMERIC_COLUMNS:
            numero = float(valor)
            payload[columna] = int(numero) if numero.is_integer() else numero
        else:
            payload[columna] = valor
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--fila", type=int, default=0, help="Fila de ejemplo_prediccion.csv (0 a 4).")
    parser.add_argument("--invalida", action="store_true", help="Omite OverallQual para provocar un rechazo.")
    args = parser.parse_args()

    payload = construir_payload(args.fila)
    if args.invalida:
        payload.pop("OverallQual")

    solicitud = urllib.request.Request(
        args.url.rstrip("/") + "/predict",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(solicitud) as respuesta:
            estado, cuerpo = respuesta.status, respuesta.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        estado, cuerpo = error.code, error.read().decode("utf-8")
    except urllib.error.URLError as error:
        print(f"No se pudo conectar con la API: {error.reason}", file=sys.stderr)
        return 1

    print(f"HTTP {estado}")
    print(cuerpo)
    return 0 if estado == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
