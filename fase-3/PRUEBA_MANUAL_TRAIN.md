# Comprobación manual de `POST /train`

Se usa una copia de `v1` y `v2` (variable `MODELS_DIR`) para no agregar versiones al repositorio durante la prueba. Sin esa variable, `/train` guarda en `fase-2/models/`.

## 1. Arranque (Docker, desde la raíz del repositorio)

```bash
docker run --rm -v "$PWD:/repo" -w /repo/fase-3 python:3.12-slim sh -c \
 "pip install -q -r requirements.txt && mkdir /m && cp -r ../fase-2/models/v1 ../fase-2/models/v2 /m/ \
  && MODELS_DIR=/m uvicorn app:app --host 0.0.0.0 --port 8000"
```

## 2. Solicitudes y respuestas reales

`POST /train` con `{"seed": 123}` (sin `version`, se asigna la siguiente libre):

```json
200 {"mensaje":"Modelo entrenado y guardado correctamente.","version":"v3","artefactos":["modelo.joblib","metrics.json","metadata.json"],"metricas_dolares":{"mae":15377.238247126214,"rmse":24721.63605392982,"r2":0.9011007496981781}}
```

Repetir con `{"version": "v3"}`:

```json
409 {"detail":"La versión 'v3' ya existe y no puede sobrescribirse."}
```

Con `{"seed": "x"}`:

```json
422 {"detail":"'seed' debe ser un entero."}
```

## 3. Persistencia

Contenido de `MODELS_DIR` tras la primera solicitud: `v1/`, `v2/` (intactas) y `v3/` con `modelo.joblib`, `metrics.json` y `metadata.json`.
