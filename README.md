# Modelo Predictivo: Precio de Vivienda (Ames Housing)

**Proyecto Integrador — Modelos y Simulación de Sistemas I**

Integrantes: Dilan Holguin Mazo, Santiago Duarte Triana, Santiago Rendón Rivera

## Descripción

El objetivo es predecir el precio de venta (`SalePrice`) de viviendas residenciales en Ames, Iowa, a partir de sus características físicas, de calidad y de ubicación. Es un problema de **regresión** sobre datos de corte transversal: cada fila es una vivienda vendida.

Los datos provienen de la competencia de Kaggle [House Prices: Advanced Regression Techniques](https://www.kaggle.com/c/house-prices-advanced-regression-techniques): 1.460 viviendas y 79 variables predictoras originales (numéricas y categóricas) más la variable objetivo.

## Estructura del repositorio

```
.
├── README.md
├── requirements.txt
└── fase-1/
    ├── train.csv            # Conjunto de datos (Kaggle, train)
    ├── notebook.ipynb       # Notebook único y ejecutable con las 12 secciones (entregable principal)
    ├── EDAnotebook.ipynb    # Secciones 1-4: introducción, datos, EDA y selección de columnas
    ├── PERSONA2.ipynb       # Secciones 5-8: preparación, split, fuga de información y modelo base
    ├── PERSONA3.ipynb       # Secciones 9-12: regresión lineal, evaluación, interpretación y guardado
    └── modelo.joblib        # Modelo final entrenado (Pipeline preprocesamiento + Regresión Lineal)
```

`notebook.ipynb` integra, en un solo archivo y en orden, el contenido de los tres notebooks individuales, y es el que debe ejecutarse de principio a fin para reproducir todo el análisis. Los notebooks individuales (`EDAnotebook.ipynb`, `PERSONA2.ipynb`, `PERSONA3.ipynb`) se conservan como registro del trabajo de cada integrante durante el desarrollo.

## Metodología (Fase 1)

1. **Introducción y descripción de los datos.**
2. **Análisis exploratorio (EDA):** valores faltantes, distribución de `SalePrice` (sesgada a la derecha → se usa `log1p(SalePrice)`), relaciones con las predictoras, correlaciones y variables con varianza casi nula.
3. **Selección de columnas:** se eliminan 18 columnas (identificador `Id`, variables casi constantes, redundantes por alta correlación entre sí, o con demasiados faltantes sin significado claro), quedando **62 variables predictoras** de las 79 originales. Todas las decisiones están justificadas con evidencia del EDA.
4. **Preparación de datos**, aplicada sobre el conjunto ya filtrado (`df_seleccionado`):
   - Faltantes que significan *ausencia* de la característica (sin sótano, sin garaje, etc.) → `'None'`.
   - Faltantes reales → mediana (numéricas) o moda (categóricas).
   - Variables de calidad (`ExterQual`, `ExterCond`, `HeatingQC`, `KitchenQual`) → codificación ordinal; nominales → one-hot.
5. **Separación entrenamiento/prueba:** `train_test_split` 80 % / 20 %, `random_state=42`.
6. **Prevención de fuga de información:** todo el preprocesamiento vive en un `ColumnTransformer` que se ajusta **solo** con el conjunto de entrenamiento.
7. **Modelo base:** `DummyRegressor` (predice siempre la media).
8. **Modelo predictivo:** `Pipeline` = preprocesador + `LinearRegression`, entrenado sobre `log1p(SalePrice)`.
9. **Evaluación:** MAE, RMSE y R² en escala logarítmica y en dólares, comparando contra el baseline, más validación cruzada de 5 folds sobre el entrenamiento.

## Resultados

Conjunto de prueba (292 viviendas, 62 columnas predictoras → 236 tras codificación):

| Modelo | MAE ($) | RMSE ($) | R² (log) | R² ($) |
|---|---:|---:|---:|---:|
| DummyRegressor (baseline) | 59.931 | 88.271 | -0.006 | -0.016 |
| **Regresión Lineal** | **17.854** | **27.395** | **0.903** | **0.902** |

- La Regresión Lineal reduce el error del baseline en un **70 %** (MAE) y **69 %** (RMSE).
- RMSE (log) en validación cruzada (5 folds): 0.157 ± 0.021.
- Principales dificultades: un fold de validación cruzada con error notablemente más alto (posible efecto de los outliers de `GrLivArea` señalados en el EDA), alta dimensionalidad tras el one-hot encoding (236 columnas para 1.168 filas de entrenamiento) con categorías poco representadas, multicolinealidad residual entre algunas predictoras, y mayor error en viviendas con condición de venta atípica (`SaleCondition` distinto de `Normal`).
- Mejoras propuestas: investigar el efecto de las ventas atípicas, regularización (Ridge/Lasso), tratar explícitamente los outliers de `GrLivArea`, ingeniería de características, y comparar contra modelos no lineales en fases siguientes.

El análisis completo está en la sección 11 de `fase-1/notebook.ipynb`.

## Cómo ejecutar

### Google Colab (recomendado)

Abrir `fase-1/notebook.ipynb` con el botón *Open in Colab* y ejecutar todas las celdas en orden (`Runtime > Run all`). El notebook es autocontenido: no depende de los notebooks individuales.

### Local

```bash
git clone https://github.com/Dilan-Holguin/ModeloPredictivo-AmesHousing.git
cd ModeloPredictivo-AmesHousing
pip install -r requirements.txt
jupyter notebook
```

Ejecutar `fase-1/notebook.ipynb` desde la **raíz del repositorio** (las rutas son relativas, p. ej. `fase-1/train.csv`).

> **Nota:** se requiere `pandas < 3`. En pandas 3 las columnas de texto dejan de ser de tipo `object`, y `select_dtypes(include=['object'])` de la sección 7 no las detectaría.

## Uso del modelo guardado

`modelo.joblib` contiene el `Pipeline` completo, así que recibe los datos **crudos ya filtrados** (las 62 columnas de `df_seleccionado`, sin `SalePrice`) y devuelve el precio en escala logarítmica:

```python
import joblib
import numpy as np
import pandas as pd

modelo = joblib.load('fase-1/modelo.joblib')

# usar el mismo df_seleccionado generado en la sección 4 del notebook
precio = np.expm1(modelo.predict(df_seleccionado.drop(columns=['SalePrice', 'SalePrice_log']).head(3)))
print(precio)
```

El archivo incluido se generó con `scikit-learn` 1.9. Si al cargarlo hay errores por diferencia de versión (p. ej. en Colab), basta con volver a ejecutar la sección 12 para regenerarlo.

## Flujo de trabajo

| Integrante | Secciones | Rama |
|---|---|---|
| Persona 1 | 1-4 (introducción, datos, EDA, selección de columnas) | `feature/analisis-exploratorio` |
| Persona 2 | 5-8 (preparación, split, fuga de información, modelo base) | `feature/preparacion-y-modelo-base` |
| Persona 3 | 9-12 (regresión lineal, evaluación, interpretación, `joblib`) + README | `feature/modelo-y-evaluacion` |

Cada rama se integró mediante Pull Request revisado por la Persona 1. Los tres notebooks se combinaron en `notebook.ipynb` como entregable único y ejecutable, integrado en `develop` y posteriormente en `main`.
