"""Reglas deterministas de faltantes y pipeline de regresión."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder

from .config import (
    FEATURE_COLUMNS,
    NOMINAL_COLUMNS,
    NUMERIC_COLUMNS,
    ORDINAL_COLUMNS,
    QUALITY_ORDER,
    STRUCTURAL_MISSING_COLUMNS,
)


def limpiar_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte NaN en ``None`` solo cuando otra variable confirma ausencia."""
    result = df.copy()
    rules = {
        "TotalBsmtSF": ["BsmtQual", "BsmtCond", "BsmtExposure", "BsmtFinType1", "BsmtFinType2"],
        "GarageCars": ["GarageType", "GarageFinish", "GarageQual", "GarageCond"],
        "Fireplaces": ["FireplaceQu"],
        "MasVnrArea": ["MasVnrType"],
    }
    for evidence_column, missing_columns in rules.items():
        if evidence_column not in result.columns:
            continue
        structural_absence = pd.to_numeric(result[evidence_column], errors="coerce").eq(0)
        for column in missing_columns:
            if column in result.columns:
                confirmed = result[column].isna() & structural_absence
                result.loc[confirmed, column] = "None"
    return result


def transform_target(y):
    """Transforma precios a log1p antes del ajuste."""
    values = np.asarray(y, dtype=float)
    if np.any(values < 0):
        raise ValueError("SalePrice no puede contener valores negativos para log1p.")
    return np.log1p(values)


def inverse_target(y):
    """Devuelve predicciones desde log1p a dólares."""
    return np.expm1(np.asarray(y, dtype=float))


def _one_hot_encoder():
    """Crea el encoder compatible con sklearn moderno y anterior a 1.2."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # pragma: no cover - compatibility with sklearn < 1.2
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_pipeline(seed: int = 42) -> Pipeline:
    """Construye toda la limpieza, imputación y codificación en un pipeline."""
    del seed  # La regresión lineal y las transformaciones son deterministas.
    none_columns = [column for column in STRUCTURAL_MISSING_COLUMNS if column in FEATURE_COLUMNS]
    nominal_columns = [column for column in NOMINAL_COLUMNS if column not in none_columns]

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", SimpleImputer(strategy="median"), NUMERIC_COLUMNS),
            (
                "structural_categories",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", _one_hot_encoder()),
                ]),
                none_columns,
            ),
            (
                "ordinal",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OrdinalEncoder(categories=[QUALITY_ORDER] * len(ORDINAL_COLUMNS))),
                ]),
                ORDINAL_COLUMNS,
            ),
            (
                "nominal",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", _one_hot_encoder()),
                ]),
                nominal_columns,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline([
        ("clean_missing", FunctionTransformer(limpiar_faltantes, validate=False)),
        ("preprocessor", preprocessor),
        ("regressor", TransformedTargetRegressor(
            regressor=LinearRegression(),
            func=transform_target,
            inverse_func=inverse_target,
            check_inverse=False,
        )),
    ])

