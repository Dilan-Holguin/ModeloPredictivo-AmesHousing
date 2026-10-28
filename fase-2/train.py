"""Entrena, evalúa y guarda una versión reproducible de Ames Housing."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.compose import TransformedTargetRegressor

from src.config import (
    COLUMN_TYPES,
    FEATURE_COLUMNS,
    MOMENTO_ESTIMACION,
    NUMERIC_COLUMNS,
    TARGET,
)
from src.data import load_data, validate_columns, validate_numeric_columns
from src.model_io import save_version
from src.preprocessing import build_pipeline, transform_target


def _commit_reference() -> str:
    """Obtiene el commit del código local o una referencia del entorno Docker."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return os.environ.get("GIT_COMMIT", "desconocido")


def _metrics(actual_dollars, predicted_dollars, actual_log, predicted_log) -> dict:
    return {
        "dolares": {
            "mae": float(mean_absolute_error(actual_dollars, predicted_dollars)),
            "rmse": float(np.sqrt(mean_squared_error(actual_dollars, predicted_dollars))),
            "r2": float(r2_score(actual_dollars, predicted_dollars)),
        },
        "log1p": {
            "mae": float(mean_absolute_error(actual_log, predicted_log)),
            "rmse": float(np.sqrt(mean_squared_error(actual_log, predicted_log))),
            "r2": float(r2_score(actual_log, predicted_log)),
        },
    }


def train(args: argparse.Namespace) -> Path:
    """Run the full, leakage-safe training workflow and return its version path."""
    if args.target != TARGET:
        raise ValueError(f"El objetivo configurado para este proyecto es '{TARGET}'.")
    if not 0 < args.test_size < 1:
        raise ValueError("--test-size debe estar entre 0 y 1, sin incluir los extremos.")

    data = load_data(args.data)
    validate_columns(data, [args.target, *FEATURE_COLUMNS])
    validate_numeric_columns(data, NUMERIC_COLUMNS + [args.target])
    y = data[args.target].astype(float)
    if y.isna().any():
        raise ValueError(f"La variable objetivo '{args.target}' no puede tener valores nulos.")
    if (y < 0).any():
        raise ValueError(f"La variable objetivo '{args.target}' no puede ser negativa.")
    X = data.loc[:, FEATURE_COLUMNS].copy()
    X.loc[:, NUMERIC_COLUMNS] = X.loc[:, NUMERIC_COLUMNS].apply(
        lambda column: pd.to_numeric(column, errors="raise")
    )

    # El split ocurre antes de que el pipeline ajuste cualquier imputador o encoder.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed
    )
    pipeline = build_pipeline(seed=args.seed)
    pipeline.fit(X_train, y_train)

    pred_test = pipeline.predict(X_test)  # TransformedTargetRegressor devuelve dólares.
    y_test_log = transform_target(y_test)
    cleaned_test = pipeline.named_steps["clean_missing"].transform(X_test)
    transformed_test = pipeline.named_steps["preprocessor"].transform(cleaned_test)
    pred_test_log = pipeline.named_steps["regressor"].regressor_.predict(transformed_test)

    baseline = TransformedTargetRegressor(
        regressor=DummyRegressor(strategy="mean"),
        func=transform_target,
        inverse_func=np.expm1,
        check_inverse=False,
    )
    # El baseline se calcula en log1p y se invierte para comparar en ambas escalas.
    baseline.fit(X_train, y_train)
    baseline_dollars = baseline.predict(X_test)
    baseline_log = baseline.regressor_.predict(X_test)

    metrics = {
        "modelo": _metrics(y_test, pred_test, y_test_log, pred_test_log),
        "baseline_media_logaritmica": _metrics(y_test, baseline_dollars, y_test_log, baseline_log),
        "observaciones": {"total": int(len(data)), "entrenamiento": int(len(X_train)), "prueba": int(len(X_test))},
        "particion": {"estrategia": "train_test_split aleatorio", "test_size": args.test_size, "seed": args.seed},
    }
    metadata = {
        "version": args.version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "tipo_problema": "regresion",
        "target": args.target,
        "algoritmo": "LinearRegression con transformacion log1p del objetivo",
        "variables_entrada": FEATURE_COLUMNS,
        "tipos_esperados": COLUMN_TYPES,
        "parametros_modelo": {"fit_intercept": True},
        "seed": args.seed,
        "datos": {"fuente": "Ames Housing", "archivo": str(Path(args.data)), "observaciones": int(len(data))},
        "estrategia_separacion": metrics["particion"],
        "metricas_evaluacion": ["mae", "rmse", "r2", "en dolares y log1p"],
        "python_version": sys.version.split()[0],
        "scikit_learn_version": sklearn.__version__,
        "dependencias": "requirements.txt",
        "git_commit": _commit_reference(),
        "momento_estimacion": MOMENTO_ESTIMACION,
    }
    version_path = save_version(pipeline, metrics, metadata, args.output_dir, args.version)
    print(f"Versión: {args.version}")
    print(f"Observaciones: {len(data)} (entrenamiento={len(X_train)}, prueba={len(X_test)})")
    print("Métricas del modelo (dólares): " + json.dumps(metrics["modelo"]["dolares"], ensure_ascii=False))
    print("Métricas del baseline (dólares): " + json.dumps(metrics["baseline_media_logaritmica"]["dolares"], ensure_ascii=False))
    for filename in ("modelo.joblib", "metrics.json", "metadata.json"):
        print(f"Generado: {version_path / filename}")
    return version_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Ruta al CSV etiquetado de entrenamiento.")
    parser.add_argument("--target", default=TARGET, help=f"Variable objetivo (por defecto: {TARGET}).")
    parser.add_argument("--output-dir", default="models", help="Directorio donde se guardan las versiones.")
    parser.add_argument("--version", required=True, help="Identificador nuevo, por ejemplo v1.")
    parser.add_argument("--seed", type=int, default=42, help="Semilla de la partición aleatoria.")
    parser.add_argument("--test-size", type=float, default=0.2, help="Fracción reservada para prueba.")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        train(args)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

