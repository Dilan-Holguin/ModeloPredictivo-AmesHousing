"""Guardado y carga de versiones inmutables del modelo."""

import json
from pathlib import Path

import joblib


def save_version(pipeline, metrics: dict, metadata: dict, models_dir: str | Path, version: str) -> Path:
    """Guarda una versión nueva; nunca sobrescribe un identificador existente."""
    if not version or Path(version).name != version or version in {".", ".."}:
        raise ValueError("La versión debe ser un identificador simple, por ejemplo v1.")
    version_dir = Path(models_dir) / version
    try:
        version_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise FileExistsError(f"La versión '{version}' ya existe; no se sobrescribió.") from exc

    joblib.dump(pipeline, version_dir / "modelo.joblib")
    with (version_dir / "metrics.json").open("w", encoding="utf-8") as stream:
        json.dump(metrics, stream, ensure_ascii=False, indent=2, allow_nan=False)
    with (version_dir / "metadata.json").open("w", encoding="utf-8") as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return version_dir


def load_model(path: str | Path):
    """Carga un pipeline desde un archivo joblib o desde una carpeta de versión."""
    model_path = Path(path)
    if model_path.is_dir():
        model_path = model_path / "modelo.joblib"
    if not model_path.is_file():
        raise FileNotFoundError(f"No se encontró el modelo: {model_path}")
    return joblib.load(model_path)

