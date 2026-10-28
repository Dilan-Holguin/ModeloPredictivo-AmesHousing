"""Lectura única y validación de los archivos de entrada."""

from pathlib import Path

import pandas as pd

from .config import FEATURE_COLUMNS


def load_data(path: str | Path) -> pd.DataFrame:
    """Lee un CSV con la misma interpretación de nulos en train y predict."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {csv_path}")
    try:
        return pd.read_csv(csv_path, keep_default_na=True)
    except (UnicodeDecodeError, pd.errors.ParserError, OSError) as exc:
        raise ValueError(f"No se pudo leer el CSV '{csv_path}': {exc}") from exc


def validate_columns(df: pd.DataFrame, required: list[str]) -> None:
    """Lanza un error claro si el DataFrame no contiene columnas requeridas."""
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError("Faltan columnas requeridas: " + ", ".join(missing))


def validate_numeric_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Comprueba que las columnas numéricas puedan interpretarse como números."""
    for column in columns:
        if column not in df.columns:
            continue
        try:
            pd.to_numeric(df[column].dropna(), errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"La columna numérica '{column}' contiene valores no numéricos.") from exc

