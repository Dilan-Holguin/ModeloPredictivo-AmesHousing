import pandas as pd
import os

def generar_datos_prueba():
    # Asume que se ejecuta desde la raíz del proyecto
    ruta_original = 'fase-1/train.csv'
    if not os.path.exists(ruta_original):
        print(f"Error: No se encontró {ruta_original}")
        return

    df = pd.read_csv(ruta_original, keep_default_na=False)
    
    # 1. Crear sample_train.csv
    os.makedirs('tests', exist_ok=True)
    df_sample = df.sample(n=100, random_state=42)
    df_sample.to_csv('tests/sample_train.csv', index=False)
    
    # 2. Crear ejemplo_prediccion.csv
    os.makedirs('data', exist_ok=True)
    df_ejemplo = df.head(5).copy()
    df_ejemplo = df_ejemplo.drop(columns=['SalePrice', 'SaleType', 'SaleCondition'])
    df_ejemplo.to_csv('data/ejemplo_prediccion.csv', index=False)
    print("Datos de prueba generados con éxito en tests/ y data/")

if __name__ == "__main__":
    generar_datos_prueba()