import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

FASE3_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = FASE3_DIR.parent
FASE2_DIR = REPO_ROOT / "fase-2"

for path in (FASE3_DIR, FASE2_DIR):
    resolved = str(path)
    if resolved not in sys.path:
        sys.path.insert(0, resolved)

import app as api_module  # noqa: E402
from src.config import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS  # noqa: E402

client = TestClient(api_module.app)


@pytest.fixture(autouse=True)
def aislar_log_predicciones(monkeypatch, tmp_path):
    """Redirige el registro de Fase 4 a un archivo temporal durante las pruebas."""
    monkeypatch.setenv("PREDICTION_LOG_PATH", str(tmp_path / "predicciones_test.csv"))


def construir_payload_valido() -> dict:
    """Extrae un registro válido desde ejemplo_prediccion.csv respetando tipos JSON."""
    ejemplo_csv = FASE2_DIR / "data" / "ejemplo_prediccion.csv"
    df = pd.read_csv(ejemplo_csv, keep_default_na=False)
    fila = df.iloc[0].to_dict()

    payload = {}
    for col in FEATURE_COLUMNS:
        val = fila[col]
        if col in NUMERIC_COLUMNS:
            if val in ("", "NA", "nan", "NaN"):
                payload[col] = None
            else:
                num = float(val)
                payload[col] = int(num) if num.is_integer() else num
        elif col in CATEGORICAL_COLUMNS:
            if val in ("", "NA", "nan", "NaN"):
                payload[col] = None
            else:
                payload[col] = str(val)
    return payload


def test_health():
    """1. GET /health devuelve HTTP 200 y un JSON de estado."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_valido():
    """2. POST /predict con entrada válida devuelve predicción en dólares y versión."""
    payload = construir_payload_valido()
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "prediccion" in body
    assert isinstance(body["prediccion"], (int, float))
    assert body["prediccion"] > 0
    assert body["version"] == "v1"


def test_predict_campo_obligatorio_ausente():
    """3. POST /predict rechaza con 422 e indica el campo cuando falta una variable requerida."""
    payload = construir_payload_valido()
    campo_faltante = "OverallQual"
    payload.pop(campo_faltante)

    response = client.post("/predict", json=payload)
    assert response.status_code in (400, 422)
    assert campo_faltante in response.json()["detail"]
