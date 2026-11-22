"""API REST para consultar el modelo Ames Housing de la Fase 2."""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any
import re
import threading
from argparse import Namespace

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
from train import train as run_training  # noqa: E402


DEFAULT_MODEL_PATH = PHASE2_PATH / "models" / "v1" / "modelo.joblib"
MODEL_PATH_ENV = "MODEL_PATH"
MODELS_DIR_ENV = "MODELS_DIR"
TRAIN_DATA_ENV = "TRAIN_DATA_PATH"
DEFAULT_MODELS_DIR = PHASE2_PATH / "models"
DEFAULT_TRAIN_DATA = PHASE2_PATH / "data" / "train.csv"
_TRAIN_LOCK = threading.Lock()
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


def _resolve(env_name: str, default: Path) -> Path:
    configured = Path(os.environ.get(env_name, str(default)))
    return configured if configured.is_absolute() else REPOSITORY_ROOT / configured


def _next_version(models_dir: Path) -> str:
    """Devuelve el siguiente identificador vN libre (ignora carpetas no numeradas)."""
    numbers = [
        int(match.group(1))
        for entry in models_dir.glob("v*")
        if entry.is_dir() and (match := re.fullmatch(r"v(\d+)", entry.name))
    ]
    return f"v{max(numbers, default=0) + 1}"


@app.post("/train")
async def train_model(request: Request) -> JSONResponse:
    """Entrena con la configuración de Fase 2 y guarda una versión nueva e inmutable.

    Cuerpo JSON opcional: {"version": "v3", "seed": 42, "test_size": 0.2}.
    """
    raw = await request.body()
    try:
        options = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"detail": "El cuerpo de la solicitud no contiene JSON válido."}, status_code=422)
    if not isinstance(options, dict):
        return JSONResponse({"detail": "El cuerpo debe ser un objeto JSON."}, status_code=422)

    seed = options.get("seed", 42)
    test_size = options.get("test_size", 0.2)
    version = options.get("version")
    if isinstance(seed, bool) or not isinstance(seed, int):
        return JSONResponse({"detail": "'seed' debe ser un entero."}, status_code=422)
    if isinstance(test_size, bool) or not isinstance(test_size, (int, float)) or not 0 < test_size < 1:
        return JSONResponse({"detail": "'test_size' debe ser un número entre 0 y 1."}, status_code=422)
    if version is not None and (not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", version)):
        return JSONResponse({"detail": "'version' debe ser un texto simple, por ejemplo v3."}, status_code=422)

    models_dir = _resolve(MODELS_DIR_ENV, DEFAULT_MODELS_DIR)
    data_path = _resolve(TRAIN_DATA_ENV, DEFAULT_TRAIN_DATA)

    with _TRAIN_LOCK:  # evita que dos entrenamientos elijan la misma versión
        version = version or _next_version(models_dir)
        if (models_dir / version).exists():
            return JSONResponse(
                {"detail": f"La versión '{version}' ya existe y no puede sobrescribirse."},
                status_code=409,
            )
        args = Namespace(
            data=str(data_path), target="SalePrice", output_dir=str(models_dir),
            version=version, seed=seed, test_size=float(test_size),
        )
        try:
            version_path = run_training(args)
        except FileNotFoundError as exc:
            return JSONResponse({"detail": f"No se encontraron los datos de entrenamiento: {exc}"}, status_code=503)
        except FileExistsError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=409)
        except ValueError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        except Exception:
            return JSONResponse({"detail": "El entrenamiento falló."}, status_code=500)

    metrics = json.loads((version_path / "metrics.json").read_text(encoding="utf-8"))
    return JSONResponse(
        {
            "mensaje": "Modelo entrenado y guardado correctamente.",
            "version": version,
            "artefactos": ["modelo.joblib", "metrics.json", "metadata.json"],
            "metricas_dolares": metrics["modelo"]["dolares"],
        },
        status_code=200,
    )
