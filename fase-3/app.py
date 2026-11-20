"""API REST para consultar el modelo Ames Housing de la Fase 2."""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any
import re
import subprocess

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PHASE2_PATH = REPOSITORY_ROOT / "fase-2"
PHASE4_PATH = REPOSITORY_ROOT / "fase-4"

# fase-2/src is intentionally reused as the only schema/model implementation.
for import_path in (PHASE2_PATH, PHASE4_PATH):
    resolved = str(import_path)
    if resolved not in sys.path:
        sys.path.insert(0, resolved)

from request_log import append_request_event  # noqa: E402
from src.config import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS  # noqa: E402
from src.data import validate_columns, validate_numeric_columns  # noqa: E402
from src.model_io import load_model  # noqa: E402
from src.preprocessing import limpiar_faltantes  # noqa: E402


DEFAULT_MODEL_PATH = PHASE2_PATH / "models" / "v1" / "modelo.joblib"
MODEL_PATH_ENV = "MODEL_PATH"
app = FastAPI(title="Ames Housing API", version="1.0.0")


def _configured_model_path() -> Path:
    configured = Path(os.environ.get(MODEL_PATH_ENV, str(DEFAULT_MODEL_PATH)))
    if not configured.is_absolute():
        configured = REPOSITORY_ROOT / configured
    return configured


def _version_from_path(model_path: Path) -> str:
    if model_path.name == "modelo.joblib":
        return model_path.parent.name
    return model_path.name


def _recorded_response(
    status_code: int,
    *,
    detail: str | None = None,
    prediction: float | None = None,
    version: str = "",
) -> JSONResponse:
    append_request_event(
        status_code=status_code,
        version=version,
        prediction=prediction,
    )
    if status_code == 200:
        return JSONResponse(
            {"prediccion": prediction, "version": version},
            status_code=status_code,
        )
    return JSONResponse({"detail": detail or "Error en la solicitud."}, status_code=status_code)


def _validate_payload(payload: Any) -> tuple[pd.DataFrame | None, str | None]:
    if not isinstance(payload, dict):
        return None, "El cuerpo debe ser un objeto JSON con las variables predictoras."

    missing = [column for column in FEATURE_COLUMNS if column not in payload]
    if missing:
        return None, "Faltan columnas requeridas: " + ", ".join(missing)

    for column in NUMERIC_COLUMNS:
        value = payload[column]
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None, f"La variable numérica '{column}' debe enviarse como número o null."
        if not math.isfinite(float(value)):
            return None, f"La variable numérica '{column}' debe ser un número finito."

    for column in CATEGORICAL_COLUMNS:
        value = payload[column]
        if value is not None and not isinstance(value, str):
            return None, f"La variable categórica '{column}' debe enviarse como texto o null."

    # Extra fields (for example Id) are accepted but never passed to the model.
    frame = pd.DataFrame([{column: payload[column] for column in FEATURE_COLUMNS}])
    try:
        validate_columns(frame, FEATURE_COLUMNS)
        validate_numeric_columns(frame, NUMERIC_COLUMNS)
    except ValueError as exc:
        return None, str(exc)

    return limpiar_faltantes(frame), None


@app.get("/health")
def health() -> dict[str, str]:
    """Indica que el proceso de la API está activo."""
    return {"status": "ok"}


@app.post("/predict")
async def predict(request: Request) -> JSONResponse:
    """Valida un registro y devuelve predicción y versión del modelo."""
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return _recorded_response(422, detail="El cuerpo de la solicitud no contiene JSON válido.")

    frame, validation_error = _validate_payload(payload)
    if validation_error:
        return _recorded_response(422, detail=validation_error)

    model_path = _configured_model_path()
    try:
        model = load_model(model_path)
    except Exception as exc:
        return _recorded_response(
            503,
            detail=f"El modelo configurado no está disponible: {exc}",
        )

    version = _version_from_path(model_path)
    try:
        prediction = float(model.predict(frame)[0])
    except (TypeError, ValueError) as exc:
        # Ordinal categories are intentionally validated by the saved encoder.
        return _recorded_response(
            422,
            detail=f"La entrada contiene una categoría o valor no admitido: {exc}",
            version=version,
        )
    except Exception:
        return _recorded_response(
            500,
            detail="No se pudo calcular la predicción con el modelo configurado.",
            version=version,
        )

    if not math.isfinite(prediction):
        return _recorded_response(
            500,
            detail="El modelo produjo una predicción no finita.",
            version=version,
        )

    return _recorded_response(200, prediction=prediction, version=version)
