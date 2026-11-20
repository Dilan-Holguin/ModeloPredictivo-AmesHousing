# Comprobación manual de `POST /train`

## 1. Arranque del servidor

Desde el directorio `fase-3/`, iniciar la API con Uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## 2. Solicitud de entrenamiento de una nueva versión

En una segunda terminal, enviar una petición `POST` al endpoint `/train` indicando una semilla aleatoria (al omitir `version`, el servicio asigna automáticamente la siguiente versión disponible, `v3`):

**Con `curl`:**
```bash
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{"seed": 123}'
```

**Con PowerShell (`Invoke-RestMethod`):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/train" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"seed": 123}' | ConvertTo-Json
```

## 3. Respuesta HTTP 200 obtenida

```json
{
  "mensaje": "Modelo entrenado y guardado correctamente.",
  "version": "v3",
  "artefactos": [
    "modelo.joblib",
    "metrics.json",
    "metadata.json"
  ]
}
```

## 4. Verificación de persistencia y conservación de versiones anteriores

Al inspeccionar el directorio de modelos (`fase-2/models/`):

```text
fase-2/models/
├── v1/
│   ├── metadata.json
│   ├── metrics.json
│   └── modelo.joblib
├── v2/
│   ├── metadata.json
│   ├── metrics.json
│   └── modelo.joblib
└── v3/
    ├── metadata.json
    ├── metrics.json
    └── modelo.joblib
```

- Las versiones previas (`v1` y `v2`) se conservan intactas.
- La nueva versión (`v3`) persiste en disco con su modelo serializado, métricas y metadatos completos.
- Si se envía nuevamente una solicitud con `"version": "v3"`, la API rechaza la sobrescritura devolviendo **HTTP 409 Conflict** (`"La versión 'v3' ya existe y no puede sobrescribirse."`).
