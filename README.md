# Modelo Predictivo: Precio de Vivienda (Ames Housing)

**Proyecto Integrador — Modelos y Simulación de Sistemas I**

Integrantes: Dilan Holguin Mazo, Santiago Duarte Triana, Santiago Rendón Rivera

## Descripción

El objetivo es predecir el precio de venta (`SalePrice`) de viviendas residenciales en Ames, Iowa, a partir de sus características físicas, de calidad y de ubicación. Es un problema de **regresión** sobre datos de corte transversal: cada fila es una vivienda vendida.

Los datos provienen de la competencia de Kaggle [House Prices: Advanced Regression Techniques](https://www.kaggle.com/c/house-prices-advanced-regression-techniques): 1.460 viviendas y 79 variables predictoras (numéricas y categóricas) más la variable objetivo.

## Estructura del repositorio

```
.
├── README.md
├── requirements.txt
└── fase-1/
    ├── train.csv            # Conjunto de datos (Kaggle, train)
    ├── EDAnotebook.ipynb    # Secciones 1-4: introducción, datos, EDA y selección de columnas
    ├── PERSONA2.ipynb       # Secciones 5-8: preparación, split, fuga de información y modelo base
    ├── PERSONA3.ipynb       # Secciones 9-12: regresión lineal, evaluación, interpretación y guardado
    └── modelo.joblib        # Modelo final entrenado (Pipeline preprocesamiento + Regresión Lineal)
```

Los notebooks se ejecutan **en ese orden** y comparten variables (por ejemplo, `df` se crea en `EDAnotebook.ipynb`, y `X_train`, `preprocessor` y `dummy_regr` en `PERSONA2.ipynb`).

## Metodología (Fase 1)

1. **Introducción y descripción de los datos.**
2. **Análisis exploratorio (EDA):** valores faltantes, distribución de `SalePrice` (sesgada a la derecha → se usa `log1p(SalePrice)`), relaciones con las predictoras, correlaciones y variables con varianza casi nula.
3. **Selección de columnas:** se justifican las columnas a eliminar (identificadores, variables casi constantes, redundantes o con demasiados faltantes).
4. **Preparación de datos:**
   - Faltantes que significan *ausencia* de la característica (sin sótano, sin garaje, etc.) → `'None'`.
   - Faltantes reales → mediana (numéricas) o moda (categóricas).
   - Variables de calidad (`ExterQual`, `ExterCond`, `HeatingQC`, `KitchenQual`) → codificación ordinal; nominales → one-hot.
5. **Separación entrenamiento/prueba:** `train_test_split` 80 % / 20 %, `random_state=42`.
6. **Prevención de fuga de información:** todo el preprocesamiento vive en un `ColumnTransformer` que se ajusta **solo** con el conjunto de entrenamiento.
7. **Modelo base:** `DummyRegressor` (predice siempre la media).
8. **Modelo predictivo:** `Pipeline` = preprocesador + `LinearRegression`, entrenado sobre `log1p(SalePrice)`.
9. **Evaluación:** MAE, RMSE y R² en escala logarítmica y en dólares, comparando contra el baseline, más validación cruzada de 5 folds sobre el entrenamiento.

## Resultados

Conjunto de prueba (292 viviendas):

| Modelo | MAE ($) | RMSE ($) | R² (log) | R² ($) |
|---|---:|---:|---:|---:|
| DummyRegressor (baseline) | 59.931 | 88.271 | -0.006 | -0.016 |
| **Regresión Lineal** | **15.394** | **23.241** | **0.910** | **0.930** |

- La Regresión Lineal reduce el error del baseline en un **74 %** (MAE y RMSE).
- RMSE (log): 0.093 en entrenamiento, 0.130 en prueba y 0.165 ± 0.023 en validación cruzada (5 folds).
- Principales dificultades: dos outliers de `GrLivArea` (casas muy grandes con precio bajo) a los que el modelo es muy sensible, 283 columnas tras el one-hot para 1.168 filas de entrenamiento (algo de sobreajuste) y multicolinealidad entre predictoras.
- Mejoras propuestas: aplicar la selección de columnas de la sección 4, regularización (Ridge/Lasso), tratar outliers, ingeniería de características y modelos no lineales en fases siguientes.

El análisis completo está en la sección 11 de `fase-1/PERSONA3.ipynb`.

## Cómo ejecutar

### Google Colab (recomendado)

Abrir `fase-1/EDAnotebook.ipynb` con el botón *Open in Colab*: las primeras celdas clonan el repositorio y se ubican en la raíz. Después ejecutar las celdas de `PERSONA2.ipynb` y `PERSONA3.ipynb` en la misma sesión.

### Local

```bash
git clone https://github.com/Dilan-Holguin/ModeloPredictivo-AmesHousing.git
cd ModeloPredictivo-AmesHousing
pip install -r requirements.txt
jupyter notebook
```

Ejecutar los notebooks desde la **raíz del repositorio** (las rutas son relativas, p. ej. `fase-1/train.csv`) y omitir las celdas de `git clone` / `%cd` pensadas para Colab.

> **Nota:** se requiere `pandas < 3`. En pandas 3 las columnas de texto dejan de ser de tipo `object`, y `select_dtypes(include=['object'])` de la sección 7 no las detectaría.

## Uso del modelo guardado

`modelo.joblib` contiene el `Pipeline` completo, así que recibe los datos **crudos** (mismas columnas que `train.csv`, sin `SalePrice`) y devuelve el precio en escala logarítmica:

```python
import joblib
import numpy as np
import pandas as pd

modelo = joblib.load('fase-1/modelo.joblib')

viviendas = pd.read_csv('fase-1/train.csv').drop(columns=['SalePrice']).head(3)
precio = np.expm1(modelo.predict(viviendas))  # revertir log1p
print(precio)
```

El archivo incluido se generó con `scikit-learn` 1.9. Si al cargarlo hay errores por diferencia de versión (p. ej. en Colab), basta con volver a ejecutar la sección 12 para regenerarlo.

## Flujo de trabajo

| Integrante | Secciones | Rama |
|---|---|---|
| Persona 1 | 1-4 (introducción, datos, EDA, selección de columnas) | `feature/analisis-exploratorio` |
| Persona 2 | 5-8 (preparación, split, fuga de información, modelo base) | `feature/preparacion-y-modelo-base` |
| Persona 3 | 9-12 (regresión lineal, evaluación, interpretación, `joblib`) + README | `feature/modelo-y-evaluacion` |

Cada rama se integra mediante Pull Request revisado por la Persona 1, y al final `develop` se integra en `main`.
