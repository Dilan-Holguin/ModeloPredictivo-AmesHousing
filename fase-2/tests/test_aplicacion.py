import subprocess
import sys
import pandas as pd
import numpy as np
from pathlib import Path

def test_entrenar_y_guardar(tmp_path):
    out_dir = tmp_path / "models"
    out_dir.mkdir()
    result = subprocess.run([
        sys.executable, "train.py",
        "--data", "tests/sample_train.csv",
        "--target", "SalePrice",
        "--output-dir", str(out_dir),
        "--version", "v_test",
        "--seed", "42"
    ], capture_output=True)
    
    assert result.returncode == 0
    assert (out_dir / "v_test" / "modelo.joblib").exists()
    assert (out_dir / "v_test" / "metrics.json").exists()
    assert (out_dir / "v_test" / "metadata.json").exists()

def test_cargar_y_predecir(tmp_path):
    out_dir = tmp_path / "models"
    out_dir.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "train.py", "--data", "tests/sample_train.csv", "--target", "SalePrice", "--output-dir", str(out_dir), "--version", "v_test", "--seed", "42"])

    in_csv = "data/ejemplo_prediccion.csv"
    out_csv = tmp_path / "prediccion_out.csv"
    result = subprocess.run([
        sys.executable, "predict.py",
        "--model", str(out_dir / "v_test" / "modelo.joblib"),
        "--input", in_csv,
        "--output", str(out_csv)
    ], capture_output=True)

    assert result.returncode == 0
    assert out_csv.exists()
    df_in = pd.read_csv(in_csv)
    df_out = pd.read_csv(out_csv)
    assert len(df_in) == len(df_out)
    assert "prediccion" in df_out.columns

def test_nulos_permitidos(tmp_path):
    out_dir = tmp_path / "models"
    out_dir.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "train.py", "--data", "tests/sample_train.csv", "--target", "SalePrice", "--output-dir", str(out_dir), "--version", "v_test"])

    df_in = pd.read_csv("data/ejemplo_prediccion.csv")
    df_in.loc[0, 'MasVnrArea'] = np.nan 
    in_csv = tmp_path / "nulos_in.csv"
    df_in.to_csv(in_csv, index=False)
    out_csv = tmp_path / "nulos_out.csv"
    
    result = subprocess.run([
        sys.executable, "predict.py",
        "--model", str(out_dir / "v_test" / "modelo.joblib"),
        "--input", str(in_csv),
        "--output", str(out_csv)
    ], capture_output=True)
    assert result.returncode == 0

def test_entrada_invalida(tmp_path):
    df_in = pd.read_csv("data/ejemplo_prediccion.csv")
    df_in = df_in.drop(columns=['OverallQual']) 
    in_csv = tmp_path / "invalido_in.csv"
    df_in.to_csv(in_csv, index=False)
    out_csv = tmp_path / "invalido_out.csv"
    
    result = subprocess.run([
        sys.executable, "predict.py",
        "--model", "dummy_path.joblib",
        "--input", str(in_csv),
        "--output", str(out_csv)
    ], capture_output=True, text=True)

    assert result.returncode != 0
    assert "Error" in result.stderr

def test_versionamiento_no_sobrescribe(tmp_path):
    out_dir = tmp_path / "models"
    out_dir.mkdir()
    
    subprocess.run([sys.executable, "train.py", "--data", "tests/sample_train.csv", "--target", "SalePrice", "--output-dir", str(out_dir), "--version", "v_test"])
    
    result = subprocess.run([
        sys.executable, "train.py",
        "--data", "tests/sample_train.csv",
        "--target", "SalePrice",
        "--output-dir", str(out_dir),
        "--version", "v_test"
    ], capture_output=True)
    
    assert result.returncode != 0
