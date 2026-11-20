"""Registro persistente de intentos al endpoint de predicción."""

from __future__ import annotations

import csv
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


FIELDS = ("fecha_hora", "estado_http", "version", "prediccion")
_WRITE_LOCK = threading.Lock()
_DEFAULT_LOG = Path(__file__).resolve().parent / "logs" / "predicciones.csv"


def _log_path(path: str | Path | None = None) -> Path:
    configured = path or os.environ.get("PREDICTION_LOG_PATH")
    if configured is None:
        return _DEFAULT_LOG

    target = Path(configured)
    if not target.is_absolute():
        target = Path(__file__).resolve().parents[1] / target
    return target


def append_request_event(
    *,
    status_code: int,
    version: str = "",
    prediction: float | None = None,
    path: str | Path | None = None,
) -> Path:
    """Agrega una fila por intento y escribe encabezado solo al crear el CSV."""
    target = _log_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    with _WRITE_LOCK:
        needs_header = not target.exists() or target.stat().st_size == 0
        with target.open("a", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            if needs_header:
                writer.writeheader()
            writer.writerow(
                {
                    "fecha_hora": timestamp,
                    "estado_http": status_code,
                    "version": version,
                    "prediccion": "" if prediction is None else prediction,
                }
            )

    return target
