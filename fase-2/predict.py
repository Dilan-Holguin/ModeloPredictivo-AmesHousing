import argparse
import sys
import pandas as pd
from src.data import load_data, validate_columns
from src.preprocessing import limpiar_faltantes
from src.model_io import load_model
from src.config import FEATURE_COLUMNS

def main():
    parser = argparse.ArgumentParser(description="Predicción de precios de vivienda.")
    parser.add_argument('--model', required=True, help="Ruta al modelo (ej. models/v1/modelo.joblib)")
    parser.add_argument('--input', required=True, help="Ruta al CSV de entrada")
    parser.add_argument('--output', required=True, help="Ruta al CSV de salida")
    args = parser.parse_args()

    try:
        df = load_data(args.input)
        validate_columns(df, FEATURE_COLUMNS)

        ids = df['Id'] if 'Id' in df.columns else pd.Series(range(1, len(df) + 1), name='Id')

        df_clean = limpiar_faltantes(df)
        pipeline = load_model(args.model)

        prediccion_dolares = pipeline.predict(df_clean)

        df_out = pd.DataFrame({'Id': ids, 'prediccion': prediccion_dolares})
        df_out.to_csv(args.output, index=False)

    except ValueError as e:
        print(f"Error de validación: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
