# Fase 4: monitoreo de `/predict`

## Registro

`fase-4/request_log.py` agrega una fila a `fase-4/logs/predicciones.csv` por **cada intento** de `/predict` (aceptado o rechazado). Campos: `fecha_hora` (UTC), `estado_http`, `version`, `prediccion` (vacías si no hubo predicción). El archivo se crea con encabezado y se conserva entre ejecuciones gracias al montaje `-v fase-4/logs:/app/fase-4/logs`.

## Monitor

```powershell
docker run --rm -v "${PWD}/fase-4/logs:/app/fase-4/logs" ames-api python ../fase-4/monitor.py
```

Muestra total de solicitudes y porcentaje de fallos 4xx/5xx. Con el registro vacío imprime `Total de solicitudes: 0` y `sin solicitudes`.

## Reporte de una ejecución real

Contenedor con `ames-api` y registro inicialmente vacío (monitor: `Total de solicitudes: 0` / `sin solicitudes`).

**Ejecución 1: API con v2** (`MODEL_PATH=fase-2/models/v2/modelo.joblib`), 3 solicitudes con `client.py`: filas 0 y 1 válidas y una inválida (`--invalida`).

| Solicitud | HTTP | Respuesta |
|---|---|---|
| fila 0 | 200 | `{"prediccion":205619.13567352018,"version":"v2"}` |
| fila 1 | 200 | `{"prediccion":199948.9513532222,"version":"v2"}` |
| sin `OverallQual` | 422 | `{"detail":"Faltan columnas requeridas: OverallQual"}` |

Monitor tras la ejecución 1:

```text
Total de solicitudes: 3
Fallos HTTP 4xx/5xx: 1 (33,3 %)
```

**Ejecución 2: vuelta a v1** (contenedor reiniciado con `MODEL_PATH=fase-2/models/v1/modelo.joblib` y el mismo volumen), 1 solicitud válida: `200 {"prediccion":208269.36445906098,"version":"v1"}`. Monitor:

```text
Total de solicitudes: 4
Fallos HTTP 4xx/5xx: 1 (25,0 %)
```

Muestra del registro (`predicciones.csv` completo):

```text
fecha_hora,estado_http,version,prediccion
2026-11-22T17:28:51.814374+00:00,200,v2,205619.13567352018
2026-11-22T17:28:52.276577+00:00,200,v2,199948.9513532222
2026-11-22T17:28:52.722045+00:00,422,,
2026-11-22T17:29:09.114042+00:00,200,v1,208269.36445906098
```

Datos observados: 3 solicitudes enviadas en la ejecución 1, 3 filas guardadas, 1 fallo = 33,3 %. Tras reiniciar el contenedor el registro conservó esas 3 filas y sumó la cuarta (sin duplicados ni pérdidas); el 25,0 % es 1 fallo en 4. La solicitud rechazada tiene versión y predicción vacías porque falló antes de usar el modelo.

## Versiones: cuál usa la API y cómo volver a la anterior

Se reutilizan las dos versiones de Fase 2: **v1** (por defecto) y **v2**. La API usa la indicada por `MODEL_PATH`; la respuesta de `/predict` y la columna `version` del registro dicen cuál. Para volver a la anterior (v2 a v1), reiniciar el contenedor con la otra ruta:

```powershell
docker rm -f ames
docker run -d --name ames -p 8000:8000 -e MODEL_PATH=fase-2/models/v1/modelo.joblib `
  -v "${PWD}/fase-2/models:/app/fase-2/models" -v "${PWD}/fase-4/logs:/app/fase-4/logs" ames-api
```

## Política de reentrenamiento

Reentrenar con `POST /train` cuando haya datos etiquetados nuevos o cuando el porcentaje de fallos 4xx/5xx del monitor supere el 10 % de forma sostenida. La versión nueva se compara con v1 y v2 mediante sus `metrics.json` y solo pasa a ser la usada por la API si mejora el RMSE en dólares; si no, se mantiene la versión previa, que siempre queda disponible para volver atrás.
