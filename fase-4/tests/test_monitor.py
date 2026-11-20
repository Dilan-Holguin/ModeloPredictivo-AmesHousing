import csv
import subprocess
import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

FASE4_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = FASE4_DIR.parent
FASE3_DIR = REPO_ROOT / "fase-3"
FASE2_DIR = REPO_ROOT / "fase-2"

for path in (FASE4_DIR, FASE3_DIR, FASE2_DIR):
    resolved = str(path)
    if resolved not in sys.path:
        sys.path.insert(0, resolved)

import app as api_module  # noqa: E402
from monitor import analizar_registro  # noqa: E402
from src.config import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS  # noqa: E402


def _payload_valido(fila_idx: int = 0) -> dict:
    ejemplo_csv = FASE2_DIR / "data" / "ejemplo_prediccion.csv"
    df = pd.read_csv(ejemplo_csv, keep_default_na=False)
    fila = df.iloc[fila_idx].to_dict()

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


def test_monitor_registro_vacio(tmp_path):
    """Con registro inexistente o solo con encabezado debe mostrar 0 y 'sin solicitudes'."""
    log_vacio = tmp_path / "predicciones_vacio.csv"
    log_vacio.write_text("fecha_hora,estado_http,version,prediccion\n", encoding="utf-8")

    res = analizar_registro(log_vacio)
    assert res["total"] == 0
    assert res["estado"] == "sin solicitudes"

    proc = subprocess.run(
        [sys.executable, str(FASE4_DIR / "monitor.py"), "--log", str(log_vacio)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "Total de solicitudes: 0" in proc.stdout
    assert "sin solicitudes" in proc.stdout


def test_monitor_dos_validas_una_invalida(monkeypatch, tmp_path):
    """Dos predicciones válidas (200) y una inválida (422) -> 3 filas y 33,3 % de fallos."""
    log_file = tmp_path / "predicciones.csv"
    monkeypatch.setenv("PREDICTION_LOG_PATH", str(log_file))

    client = TestClient(api_module.app)

    # 2 solicitudes válidas
    r1 = client.post("/predict", json=_payload_valido(0))
    r2 = client.post("/predict", json=_payload_valido(1))
    assert r1.status_code == 200
    assert r2.status_code == 200

    # 1 solicitud inválida (falta columna requerida)
    invalido = _payload_valido(0)
    invalido.pop("OverallQual")
    r3 = client.post("/predict", json=invalido)
    assert r3.status_code == 422

    # Verificar que se guardaron exactamente 3 filas
    with log_file.open("r", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 3

    # Verificar el cálculo y la salida del monitor
    res = analizar_registro(log_file)
    assert res["total"] == 3
    assert res["fallos"] == 1
    assert res["porcentaje_fallos"] == 33.3

    proc = subprocess.run(
        [sys.executable, str(FASE4_DIR / "monitor.py"), "--log", str(log_file)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "Total de solicitudes: 3" in proc.stdout
    assert "33,3 %" in proc.stdout
