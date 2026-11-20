# Plan de trabajo para las fases 3 y 4

Este plan convierte la retroalimentación de la Fase 2 y las especificaciones del profesor en tareas asignadas y una secuencia de integración. La Fase 2 obtuvo 100/100 (5,00/5,00) y el profesor no señaló faltantes sustanciales. La prioridad es conservar su comportamiento y añadir la API y el monitoreo pedidos.

## Reglas que deben mantenerse

- Conservar `fase-1/` y `fase-2/`, los modelos v1 y v2, sus métricas y metadatos.
- Mantener las reglas de faltantes estructurales en sótanos, garajes y mampostería. No cambiar el algoritmo ni las métricas de referencia como parte de estas fases.
- Cuando cambie la aplicación, volver a ejecutar pruebas y comparar la predicción de una entrada conocida con la versión anterior. Explicar cualquier diferencia.
- Cada integrante trabaja en su rama y abre un PR revisado hacia `develop`. Al finalizar, integrar `develop` en `main` y marcar la entrega con un commit o etiqueta.

## Preparación del repositorio

Antes de iniciar la Fase 3, se sincronizó `main` con `develop` mediante el PR #16. `develop` ya incluye los cambios finales de Fase 2 en `fase-2/predict.py` y `fase-2/tests/test_aplicacion.py` y queda como base común para las nuevas ramas.

## Reparto propuesto

Los documentos del profesor describen entregables y pruebas, pero no asignan tareas por persona. Este reparto es una propuesta según los módulos y aportes previos del equipo.

### Dilan Holguín Mazo (`Dilan-Holguin`)

**Fase 3: predicción y contrato de la API**

- Crear la estructura de `fase-3/` y el contrato JSON usando las columnas de `fase-2/src/config.py`.
- Implementar `GET /health` y `POST /predict`. La predicción debe reutilizar el modelo y el preprocesamiento de Fase 2; responder con el valor y el identificador de la versión usada.
- Validar campos requeridos y tipos; admitir nulos según las reglas existentes; devolver errores comprensibles y un error de servicio si no está disponible el modelo configurado.
- Dejar por escrito el contrato de solicitud y respuesta para que el resto del equipo integre entrenamiento, cliente y pruebas.

**Fase 4: registro de solicitudes**

- Implementar el registro persistente de cada intento de `/predict`, tanto válido como rechazado, con fecha/hora, estado HTTP, versión y predicción. En errores, dejar vacíos los valores que no existan.
- Integrar el registro para que cada intento produzca exactamente una fila, incluso cuando el framework rechace la entrada antes de ejecutar la predicción.

### Santiago Rendón Rivera (`patomomo-dev`)

**Fase 3: entrenamiento y pruebas de API**

- Implementar `POST /train` reutilizando el entrenamiento de Fase 2, con los datos, objetivo y semilla del proyecto.
- Generar una versión disponible, guardar modelo, métricas y metadatos, conservar las versiones anteriores y devolver el identificador creado con HTTP 200 o 201.
- Añadir las tres pruebas requeridas con pytest: `/health` exitoso, predicción válida que devuelva predicción y versión, y rechazo de una solicitud sin un campo requerido.
- Documentar una ejecución manual de `/train` que compruebe que la nueva versión quedó guardada.

**Fase 4: métricas de operación**

- Crear un script que lea el registro y muestre total de solicitudes y porcentaje fallido; contar como fallidas las respuestas 4xx y 5xx.
- Cubrir con pruebas el registro vacío: total 0 y porcentaje informado como “sin solicitudes”.
- Verificar el caso de referencia: dos predicciones válidas y una solicitud inválida deben producir tres filas y 33,3 % de fallos.

### Santiago Duarte Triana (`santiagodutr`)

**Fase 3: Docker, cliente y guía de uso**

- Añadir en `fase-3/` el Dockerfile actualizado y las dependencias necesarias. El contenedor debe arrancar el servidor escuchando en `0.0.0.0:8000`; documentar el puerto y los montajes persistentes de datos y modelos.
- Crear un cliente pequeño en Python o un archivo de comandos `curl` que envíe al menos un registro del CSV de ejemplo a `/predict`.
- Documentar instalación, construcción y arranque del contenedor, selección de una versión, ejemplos de `/health`, `/predict` y `/train`, y la evidencia manual.

**Fase 4: persistencia en Docker y reporte**

- Montar el archivo de solicitudes en un volumen para conservarlo entre ejecuciones del contenedor.
- Añadir `fase-4/README.md` con un reporte de la corrida real: solicitudes enviadas, filas del registro, total y porcentaje fallido, explicación breve, identificadores de dos versiones y cómo volver a la versión anterior.
- Escribir una política de reentrenamiento de dos o tres frases: qué observación dispara la revisión, quién ejecuta `/train` y cómo se compara y activa la candidata. Incluir una muestra del registro.

## Orden recomendado de ramas y PRs

Todos los PR de trabajo se abren hacia `develop`; se revisan antes de fusionarlos.

1. **Completado — sincronización de ramas:** PR #16 de `main` hacia `develop`, incorporando la advertencia de columnas extra y la actualización de pruebas de Fase 2. Fusionado en `a103348`.
2. **API base — Dilan:** contrato, `/health` y `/predict`. Fusionar primero porque fija el esquema que usarán las pruebas, el cliente y el contenedor.
3. **Entrenamiento y pruebas — Santiago Rendón:** `/train` y las tres pruebas de API. Fusionar después de acordar el contrato de la API.
4. **Docker y cliente — Santiago Duarte:** Dockerfile, dependencias, cliente y README de Fase 3. Fusionar cuando las rutas y comandos estén estables.
5. **Registro — Dilan:** incorporar el registro de intentos válidos e inválidos en `/predict`, sobre la API integrada.
6. **Métricas — Santiago Rendón:** script y pruebas de monitoreo, usando el formato de registro ya acordado en el paso 5.
7. **Persistencia y reporte — Santiago Duarte:** volumen Docker, corrida de dos solicitudes válidas y una inválida, muestra del registro y reporte final. Este PR depende de los pasos 5 y 6.
8. **Cierre:** ejecutar la verificación desde una copia limpia, abrir un PR de `develop` hacia `main`, fusionarlo y marcar la entrega de Fases 3 y 4 con un identificador nuevo, sin mover ni reemplazar la etiqueta `entrega-2`.

## Lista de aceptación antes del PR final

### Fase 3

- [ ] `GET /health` devuelve HTTP 200 y un JSON de estado.
- [ ] Una predicción válida devuelve valor y versión; una entrada sin campo obligatorio devuelve 400 o 422 con el nombre del campo.
- [ ] Los tipos incompatibles y el modelo no disponible producen errores comprensibles (400/422 y 503, respectivamente).
- [ ] `/train` crea y persiste una versión nueva con sus tres artefactos y no sobrescribe versiones anteriores.
- [ ] Pasan las tres pruebas pytest indicadas.
- [ ] El cliente de ejemplo funciona contra el contenedor y el README muestra una solicitud y respuesta reales.

### Fase 4

- [ ] Cada intento de `/predict`, incluidos los rechazos, se registra una sola vez y el archivo sobrevive al reinicio del contenedor.
- [ ] El monitor calcula total y porcentaje 4xx/5xx; maneja correctamente un archivo vacío.
- [ ] El ensayo de dos solicitudes válidas y una inválida produce tres registros y 33,3 % de fallos.
- [ ] El reporte documenta la ejecución observada, la política de reentrenamiento, las dos versiones y cómo cambiar la versión activa.
- [ ] Desde una copia limpia se reconstruye el contenedor, se ejecutan pruebas y se repite la demostración.

## Alcance y calendario

Las especificaciones no fijan fechas límite ni exigen despliegue en la nube, tableros gráficos o reentrenamiento automático; esos elementos son opcionales. El equipo debe acordar las fechas según el orden y las dependencias anteriores.

## Fuentes

- Evaluación y retroalimentación de Fase 2: `G16_Dilan_Holguin_Evaluacion_Fase_2.docx`.
- Especificaciones técnicas de Fases 3 y 4: `Especificaciones_tecnicas_fases_3_y_4.pdf`.
