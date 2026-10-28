# Fase 2: scripts, versionamiento y Docker

Entrega: etiqueta Git **`entrega-2`** (rama `main`). La Fase 1 (`../fase-1/`) queda intacta como registro del análisis exploratorio.

Esta fase convierte el notebook de la Fase 1 en una aplicación reproducible: un script de entrenamiento versionado (`train.py`), un script de predicción por lotes (`predict.py`), pruebas automáticas y una imagen Docker. **No se mejora el modelo**: se conserva el enfoque de la Fase 1 (Regresión Lineal sobre `log1p(SalePrice)`) y solo se corrigen los problemas de diseño señalados por el profesor.

## Problema

Se estima el precio de venta (`SalePrice`) de viviendas de Ames, Iowa (dataset de Kaggle *House Prices*, 1.460 viviendas, años 2006-2010).

**Momento de la estimación (D1):** antes de vender la vivienda. El modelo entrega un precio de referencia para fijar un precio de salida o evaluar una oferta, usando solo información que existe en ese momento. Por eso no se usa ninguna variable que solo se conozca una vez ocurrida la venta.

## Estructura

```
fase-2/
├── train.py                 # Entrena y guarda una versión en models/<id>/
├── predict.py               # Predice sobre un CSV con un modelo guardado
├── requirements.txt         # Versiones exactas (Python 3.12)
├── Dockerfile
├── .dockerignore
├── src/
│   ├── config.py            # Esquema: columnas por tipo y columnas excluidas
│   ├── data.py              # load_data() y validate_columns()
│   ├── preprocessing.py     # limpiar_faltantes(), build_pipeline(), objetivo log1p/expm1
│   └── model_io.py          # save_version() y load_model()
├── tests/
│   ├── test_aplicacion.py   # Cinco pruebas con pytest
│   └── sample_train.csv     # Muestra pequeña para las pruebas
├── data/
│   ├── train.csv            # Copia de fase-1/train.csv (el contexto de Docker es fase-2/)
│   └── ejemplo_prediccion.csv
├── models/
│   ├── v1/                  # seed 42
│   └── v2/                  # seed 7
└── outputs/                 # Predicciones generadas (ignorado por Git)
```

Cada versión `models/<id>/` contiene `modelo.joblib`, `metrics.json` y `metadata.json`.

## Decisiones de diseño y correcciones de la Fase 1

| Corrección / decisión | Qué se hizo |
|---|---|
| **Id como predictora** (D4) | La Fase 1 entrenó con `Id`. Ahora `src/config.py` es la única fuente de verdad: listas explícitas de columnas numéricas, ordinales y nominales, sin `Id` y sin `select_dtypes` (que dependía de la versión de pandas). |
| **`SaleType` y `SaleCondition`** (D2) | Se excluyen: describen la transacción (tipo de contrato, venta normal o ejecución hipotecaria) y solo se conocen cuando la venta ya ocurrió. Usarlas es fuga de información y contradice D1. Se pasa de 62 a **60 predictoras**. La métrica puede variar un poco y se reporta tal cual. |
| **`YrSold` y `MoSold`** (D3) | Se conservan, interpretadas como la **fecha de la estimación** (momento del mercado en que se tasa). Limitación: el dataset cubre 2006-2010, así que el modelo no extrapola a otros años. |
| **Faltantes: ausencia real vs. desconocido** (D5) | Dos etapas. (a) `limpiar_faltantes`, determinista y sin aprender de los datos: un NaN pasa a `'None'` solo si otra columna lo respalda (`Bsmt*` con `TotalBsmtSF == 0`, `Garage*` con `GarageCars == 0`, `FireplaceQu` con `Fireplaces == 0`, `MasVnrType` con `MasVnrArea == 0`). (b) Dentro del `Pipeline`, lo que queda desconocido se imputa con estadísticos aprendidos solo con entrenamiento (mediana en numéricas, moda en categóricas). |
| **`MasVnrType`: 8 desconocidos** | pandas lee la palabra `None` como nulo. Por eso la columna aparecía con 59,7 % de faltantes (588 no nulos de 1.460), pero casi todos son la categoría real "sin mampostería". Evidencia más abajo. |
| **Lectura única del CSV** (D6) | `load_data` es la única función que lee CSV, tanto para entrenar como para predecir, así ambos interpretan igual `NA` y `None`. |
| **Objetivo en logaritmo** (D7) | `log1p(SalePrice)` y su inversa `expm1` se definen una sola vez en `preprocessing.py`. `metrics.json` reporta ambas escalas (log y dólares), y el README toma sus números de ahí. |
| **Baseline** (D8) | `DummyRegressor(strategy="mean")` se entrena y evalúa con la misma partición y las mismas métricas que el modelo. Al ser un promedio en escala logarítmica, al invertirlo equivale a una **media geométrica**, no al precio promedio en dólares. |
| **Partición aleatoria** (D9) | `train_test_split` 80/20 con `--seed` (por defecto 42) y `--test-size` configurables. No se separa por barrio: cada fila es la venta de una vivienda distinta y el uso real es tasar casas de barrios que el modelo ya conoce. Limitación: el dataset no trae identificador de propiedad, así que no se puede comprobar si una misma casa aparece dos veces. |
| **Trazabilidad** (D10) | Cada versión guarda en `metadata.json` el commit de Git, la semilla, los tamaños y la estrategia de partición. Una versión existente nunca se sobrescribe. |
| **Versiones fijas** (D12) | `requirements.txt` con versiones exactas e imagen `python:3.12-slim`. En la Fase 1 el modelo se guardó con scikit-learn 1.9.1 y se ejecutó con 1.8.0 porque no había versiones fijas: un `.joblib` solo es fiable con la versión que lo creó. |

### Evidencia: `MasVnrType`

```python
pd.read_csv('data/train.csv', keep_default_na=False)['MasVnrType'].value_counts()
```

```
None       864
BrkFace    445
Stone      128
BrkCmn      15
NA           8      <- los únicos desconocidos reales
```

Leído con el valor por defecto de pandas, solo hay 588 no nulos: las 864 viviendas `None` se convierten en nulos.

## Reproducir el entorno

Python **3.12** (el mismo de la imagen Docker). En PowerShell, desde la raíz del repositorio:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python --version
pip install -r fase-2/requirements.txt
cd fase-2
python -m pytest
```

## Entrenar

```powershell
python train.py --data data/train.csv --target SalePrice --output-dir models --version v1 --seed 42
python train.py --data data/train.csv --target SalePrice --output-dir models --version v2 --seed 7
python train.py --help
```

Argumentos: `--data`, `--target`, `--output-dir`, `--version` (obligatorio), `--seed` (42) y `--test-size` (0.2). Si la versión ya existe, el script termina con error y no escribe nada. **Regenerar el modelo exige ejecutar este entrenamiento**; no basta con abrir un notebook.

## Predecir

```powershell
python predict.py --model models/v1/modelo.joblib --input data/ejemplo_prediccion.csv --output outputs/predicciones.csv
python predict.py --help
```

Política de entrada:

- Falta una columna requerida: error claro, código de salida distinto de cero y no se crea el archivo de salida.
- Columnas extra: se ignoran con un aviso. Si viene `Id`, se copia a la salida pero no se usa para predecir.
- El orden de las columnas no importa.
- Las columnas numéricas deben poder convertirse a número; si no, error claro.
- Celdas nulas: permitidas, se tratan según D5.
- Categorías no vistas: el one-hot las ignora; en las 4 ordinales de calidad (`ExterQual`, `ExterCond`, `HeatingQC`, `KitchenQual`) es error.
- Salida: columna `prediccion` en **dólares**, una fila por fila de entrada y en el mismo orden. Nunca se descartan filas en silencio.

## Docker

Docker Desktop debe estar abierto. Comandos verificados en PowerShell, desde `fase-2/`:

```powershell
docker build -t modelos-fase2:1.0 .
mkdir models, outputs -Force
```

Entrenar dentro del contenedor (los modelos persisten en `models/` del anfitrión). `.dockerignore` excluye `.git`, así que el commit se pasa con `GIT_COMMIT`; si la variable no existe, `metadata.json` guarda `"desconocido"`:

```powershell
docker run --rm `
  -e "GIT_COMMIT=$(git rev-parse HEAD)" `
  -v "${PWD}/data:/app/data:ro" `
  -v "${PWD}/models:/app/models" `
  modelos-fase2:1.0 python train.py --data data/train.csv --target SalePrice --output-dir models --version v-docker
```

Predecir dentro del contenedor (el resultado queda en `outputs/` del anfitrión):

```powershell
docker run --rm `
  -v "${PWD}/data:/app/data:ro" `
  -v "${PWD}/models:/app/models:ro" `
  -v "${PWD}/outputs:/app/outputs" `
  modelos-fase2:1.0 python predict.py --model models/v-docker/modelo.joblib --input data/ejemplo_prediccion.csv --output outputs/predicciones_docker.csv
```

La imagen no entrena durante el build ni define `ENTRYPOINT`: el comando se indica en cada `docker run`. `models/v-docker/` se genera localmente y no se versiona; `models/v1` y `models/v2` sí.

## Pruebas

```powershell
python -m pytest
```

Cinco pruebas en `tests/test_aplicacion.py`, con `tmp_path` (no tocan los modelos de la entrega):

1. Entrenar y guardar: genera artefacto cargable, métricas y metadatos.
2. Cargar y predecir: una predicción por fila, igual a la previa al guardado.
3. Nulos: una entrada con nulos en una columna que los admite se procesa según D5.
4. Entrada inválida: falta una columna requerida, error claro y código de salida distinto de cero.
5. Versionamiento: la segunda versión conserva la primera y un id repetido no sobrescribe.

## Resultados

Las métricas salen de `models/<id>/metrics.json`, no de copiar números a mano. Ejemplo de la ejecución en Docker (`v-docker`, seed 42, 1.168 filas de entrenamiento y 292 de prueba, 60 predictoras):

| Modelo | MAE ($) | RMSE ($) | R² ($) | RMSE (log) | R² (log) |
|---|---:|---:|---:|---:|---:|
| Baseline (media en log) | 59.931 | 88.271 | -0,016 | 0,433 | -0,006 |
| **Regresión Lineal** | **17.896** | **27.522** | **0,901** | **0,134** | **0,904** |

Al excluir `SaleType` y `SaleCondition` y corregir `Id`, los valores difieren levemente de la Fase 1 (MAE 17.854, R² 0,902); la especificación no exige mejorarlos.

## Limitaciones

- El modelo solo vio ventas de 2006 a 2010; no extrapola a otros años (D3).
- No se puede verificar si una misma vivienda aparece más de una vez, porque el dataset no tiene identificador de propiedad (D9).
- Un solo conjunto de prueba (292 viviendas): las métricas dependen de la semilla (compárense `v1` y `v2`).
- No se hace validación cruzada ni regularización en esta fase; quedan como mejoras futuras.
