# Fase 3: API REST del modelo Ames Housing

API FastAPI que reutiliza el preprocesamiento y los modelos de `fase-2/` (v1 y v2 siguen intactos). Cada intento de `/predict` queda registrado para el monitoreo de `fase-4/`.

## Rutas

| Ruta | Descripción |
|---|---|
| `GET /health` | `200 {"status":"ok"}` |
| `POST /predict` | Recibe las 60 variables predictoras (sin `SalePrice`; campos extra como `Id` se ignoran). Los nulos (`null`) se tratan con las reglas de Fase 2. Responde `{"prediccion": <USD>, "version": "v2"}`. |
| `POST /train` | Entrena con `fase-2/data/train.csv` y guarda una versión nueva. Cuerpo opcional: `{"version":"v3","seed":42,"test_size":0.2}`. Sin `version` toma la siguiente libre. |

Errores: `422` falta una variable o tipo incompatible (el mensaje nombra el campo), `503` el modelo configurado no existe, `409` en `/train` si la versión ya existe (nunca se sobrescribe).

## Construir y arrancar

Desde la **raíz del repositorio** (el contexto necesita `fase-2` y `fase-4`):

```powershell
docker build -f fase-3/Dockerfile -t ames-api .
docker run -d --name ames -p 8000:8000 `
  -v "${PWD}/fase-2/data:/app/fase-2/data" `
  -v "${PWD}/fase-2/models:/app/fase-2/models" `
  -v "${PWD}/fase-4/logs:/app/fase-4/logs" `
  ames-api
```

(En bash use `\` en lugar de `` ` ``.) El contenedor ejecuta `uvicorn app:app --host 0.0.0.0 --port 8000`. Los tres montajes conservan datos, modelos y el registro de Fase 4 entre ejecuciones.

## Selección de versión

La API usa la variable `MODEL_PATH` (por defecto `fase-2/models/v1/modelo.joblib`). Para usar v2:

```powershell
docker rm -f ames
docker run -d --name ames -p 8000:8000 -e MODEL_PATH=fase-2/models/v2/modelo.joblib `
  -v "${PWD}/fase-2/models:/app/fase-2/models" -v "${PWD}/fase-4/logs:/app/fase-4/logs" ames-api
```

La respuesta de `/predict` incluye la versión efectivamente usada. Variables opcionales: `MODELS_DIR`, `TRAIN_DATA_PATH`, `PREDICTION_LOG_PATH`.

## Cliente y ejemplos reales

`client.py` (solo biblioteca estándar) envía una vivienda de `ejemplo_prediccion.csv`:

```powershell
python fase-3/client.py            # válida
python fase-3/client.py --invalida # omite OverallQual
curl http://localhost:8000/health
```

Con `MODEL_PATH` en v2, ejecución real:

```text
HTTP 200
{"prediccion":205619.13567352018,"version":"v2"}

HTTP 422
{"detail":"Faltan columnas requeridas: OverallQual"}
```

Modelo inexistente (`MODEL_PATH` apuntando a `v99`): `HTTP 503` con `{"detail":"El modelo configurado no está disponible: No se encontró el modelo: ..."}`.

Entrenar una versión nueva (ejecución real desde el contenedor, con una copia de v1/v2 montada):

```text
POST /train {"seed": 42}
200 {"mensaje":"Modelo entrenado y guardado correctamente.","version":"v3","artefactos":["modelo.joblib","metrics.json","metadata.json"],"metricas_dolares":{"mae":17895.73...,"rmse":27522.36...,"r2":0.9012...}}
```

La comprobación manual completa de persistencia está en [PRUEBA_MANUAL_TRAIN.md](PRUEBA_MANUAL_TRAIN.md). Con el montaje de `fase-2/models` de arriba, la versión nueva queda en el repositorio local como `fase-2/models/v3/`.

## Pruebas

```powershell
docker run --rm ames-api python -m pytest /app/fase-3 /app/fase-4 -q
```

Resultado real: `5 passed` (salud, predicción válida con versión, campo obligatorio ausente, y las dos de monitoreo).

## Comparación con Fase 2

Para la fila 0 de `ejemplo_prediccion.csv` con v1, la API devuelve `208269.36445906098`, idéntico a `fase-2/predict.py` (`208269.36445906098`). No hay diferencias.
