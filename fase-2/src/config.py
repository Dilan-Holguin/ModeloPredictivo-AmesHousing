"""Esquema y constantes compartidos de Ames Housing.

Las listas son explícitas para que el modelo no dependa de inferencias de dtype
ni incluya columnas posteriores a la venta.
"""

TARGET = "SalePrice"

# 60 predictores aprobados: 29 numéricos, 4 ordinales y 27 nominales.
NUMERIC_COLUMNS = [
    "MSSubClass", "LotFrontage", "LotArea", "OverallQual", "OverallCond",
    "YearBuilt", "YearRemodAdd", "MasVnrArea", "BsmtFinSF1", "BsmtFinSF2",
    "BsmtUnfSF", "TotalBsmtSF", "1stFlrSF", "2ndFlrSF", "GrLivArea",
    "BsmtFullBath", "FullBath", "HalfBath", "BedroomAbvGr", "KitchenAbvGr",
    "TotRmsAbvGrd", "Fireplaces", "GarageCars", "WoodDeckSF", "OpenPorchSF",
    "EnclosedPorch", "MoSold", "YrSold",
]

ORDINAL_COLUMNS = ["ExterQual", "ExterCond", "HeatingQC", "KitchenQual"]
QUALITY_ORDER = ["Po", "Fa", "TA", "Gd", "Ex"]

STRUCTURAL_MISSING_COLUMNS = [
    "BsmtQual", "BsmtCond", "BsmtExposure", "BsmtFinType1", "BsmtFinType2",
    "GarageType", "GarageFinish", "GarageQual", "GarageCond", "FireplaceQu",
    "MasVnrType",
]

NOMINAL_COLUMNS = [
    "MSZoning", "LotShape", "LandContour", "LotConfig", "LandSlope",
    "Neighborhood", "Condition1", "BldgType", "HouseStyle", "RoofStyle",
    "Exterior1st", "Exterior2nd",
    "MasVnrType", "Foundation", "BsmtQual", "BsmtCond", "BsmtExposure",
    "BsmtFinType1", "BsmtFinType2", "CentralAir", "Electrical", "Functional",
    "FireplaceQu", "GarageType", "GarageFinish", "GarageQual", "GarageCond",
    "PavedDrive",
]

# Exclusiones justificadas por D2 y por la selección de variables de Fase 1.
COLUMNAS_EXCLUIDAS = [
    "Id", "SaleType", "SaleCondition", "Street", "LowQualFinSF",
    "BsmtHalfBath", "3SsnPorch", "ScreenPorch", "MiscVal", "PoolQC",
    "PoolArea", "MiscFeature", "GarageYrBlt", "Alley", "Fence", "GarageArea",
    "Utilities", "Condition2", "RoofMatl", "Heating",
]

# Las categorías ausentes aquí se conservan como "desconocidas" y se imputan
# con la moda aprendida por el pipeline, nunca como ausencia estructural.
CATEGORICAL_COLUMNS = ORDINAL_COLUMNS + NOMINAL_COLUMNS
FEATURE_COLUMNS = NUMERIC_COLUMNS + CATEGORICAL_COLUMNS
COLUMN_TYPES = {
    **{name: "numeric" for name in NUMERIC_COLUMNS},
    **{name: "ordinal" for name in ORDINAL_COLUMNS},
    **{name: "nominal" for name in NOMINAL_COLUMNS},
}

MOMENTO_ESTIMACION = "Antes de la venta, usando solo características disponibles al tasar."

