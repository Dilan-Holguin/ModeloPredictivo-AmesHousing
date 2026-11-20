# Plan de trabajo para las fases 3 y 4

Este plan organiza el trabajo del equipo en **un PR por integrante**, incluyendo en cada PR las tareas asignadas de las dos fases. La Fase 2 obtuvo 100/100 (5,00/5,00) y el profesor no señaló faltantes sustanciales. La prioridad es conservar lo entregado y añadir la API y el monitoreo pedidos.

## Requisitos que vienen del profesor

### Mantener la Fase 2

- Conservar `fase-1/`, `fase-2/`, los modelos v1 y v2, sus métricas y metadatos.
- Mantener el tratamiento de ausencias estructurales en sótanos, garajes y mampostería.
- Al modificar la aplicación, repetir las pruebas y comparar una predicción conocida con la versión previa. Explicar cualquier diferencia.
- No es necesario cambiar de algoritmo ni mejorar las métricas para estas entregas.

### Fase 3: API REST

- Agregar `fase-3/` sin eliminar las carpetas anteriores. Se permite FastAPI o Flask.
- Exponer `GET /health`, `POST /predict` y `POST /train`.
- `/predict` recibe las variables predictoras, reutiliza el preprocesamiento y el modelo guardado, y devuelve predicción y versión usada. No recibe `SalePrice`.
- Validar campos obligatorios y tipos; aceptar nulos según las reglas de Fase 2; devolver un error comprensible al faltar el modelo configurado.
- `/train` reutiliza la configuración y datos del proyecto, guarda modelo, métricas y metadatos con una versión nueva y conserva las anteriores.
- Incluir tres pruebas pytest: salud, predicción válida con versión y rechazo de un campo obligatorio ausente. Para `/train`, documentar una prueba manual que compruebe la persistencia de la nueva versión.
- Incluir en `fase-3/` el código, dependencias, Dockerfile actualizado, pruebas, README y un cliente sencillo que envíe una predicción realista.

### Fase 4: monitoreo

- Agregar `fase-4/` y registrar cada intento de `/predict`, incluidos los rechazados, con fecha/hora, estado HTTP, versión y predicción. Conservar el registro entre ejecuciones y guardar una sola fila por solicitud.
- Crear un script que muestre total de solicitudes y porcentaje de fallos HTTP 4xx/5xx. Con registro vacío, mostrar total 0 y “sin solicitudes”.
- Reutilizar dos versiones anteriores, indicar cuál usa la API y documentar cómo volver a la anterior.
- Incluir una política breve de reentrenamiento y un reporte basado en una ejecución real.

## Estado del repositorio

`develop` ya quedó sincronizada con los cambios finales de Fase 2 mediante el PR #16. El plan fue agregado a `develop` mediante el PR #17. Las nuevas ramas de trabajo deben crearse desde la versión actualizada de `develop`.

## Reparto: un PR por integrante

El profesor define los entregables, pero no asigna tareas por persona. Este reparto es una propuesta basada en los módulos que cada integrante trabajó en Fase 2. Cada persona prepara **un solo PR** con sus contribuciones de Fase 3 y Fase 4.

### 1. Dilan Holguín Mazo (`Dilan-Holguin`)

**Responsabilidad: servicio de predicción y registro de solicitudes**

- En su PR, crear el núcleo de `fase-3/` y fijar el contrato JSON.
- Implementar `GET /health` y `POST /predict` sobre el modelo y preprocesamiento existentes. Responder con la predicción y el identificador de la versión.
- Validar las columnas y tipos requeridos, admitir nulos con las reglas de Fase 2 y responder con códigos de error comprensibles, incluyendo el caso de modelo no disponible.
- En el mismo PR, agregar el registro persistente que usará Fase 4 e integrarlo con `/predict`. Registrar solicitudes válidas y rechazadas, exactamente una vez por intento.
- Acordar y documentar el formato del registro antes de que Rendón implemente el monitor. Campos mínimos: `fecha_hora`, `estado_http`, `version`, `prediccion`.

### 2. Santiago Rendón Rivera (`patomomo-dev`)

**Responsabilidad: entrenamiento por API y métricas de monitoreo**

- En un solo PR, añadir `POST /train` reutilizando el entrenamiento de Fase 2. Generar un identificador de versión disponible, persistir los tres artefactos, conservar versiones previas y devolver el identificador.
- Añadir las tres pruebas pytest solicitadas para `/health`, `/predict` válido y campo obligatorio ausente. Documentar además una ejecución manual de `/train` que muestre la versión creada.
- En el mismo PR, crear el script que lee el registro acordado con Dilan y calcula total de solicitudes y porcentaje 4xx/5xx.
- Probar el archivo vacío y el caso de dos predicciones válidas más una inválida: tres solicitudes y 33,3 % de fallos.

### 3. Santiago Duarte Triana (`santiagodutr`)

**Responsabilidad: Docker, cliente y documentación de ambas fases**

- En un solo PR, agregar el Dockerfile de `fase-3/`, las dependencias y el cliente Python o `curl`. El contenedor debe iniciar la API en `0.0.0.0:8000`, publicar el puerto y montar datos y modelos.
- Documentar en `fase-3/README.md` la construcción, arranque, rutas, selección de versión y ejemplos reales de solicitud y respuesta.
- Extender los montajes de Docker para conservar el registro de Fase 4 entre ejecuciones.
- Crear `fase-4/README.md` con el reporte de una ejecución real, muestra del registro, las dos versiones utilizadas, cómo volver a la versión anterior y una política de reentrenamiento de dos o tres frases.
- Incluir en el reporte los datos observados: solicitudes enviadas, filas guardadas, total, porcentaje de fallos y explicación del resultado.

## Orden para trabajar y subir los PRs

Los PR de cada integrante apuntan a `develop`. El orden respeta las dependencias entre los módulos y evita trabajar sobre una base desactualizada.

1. **Completado:** PR #16 sincronizó `main` hacia `develop`; PR #17 agregó este plan.
2. **Dilan, un PR:** API `/health` y `/predict` más el registro de solicitudes de Fase 4. Fusionar primero para fijar el contrato de predicción y el formato del registro.
3. **Santiago Rendón, un PR:** `/train`, las pruebas de API, el script de monitoreo y sus pruebas. Crear la rama desde el `develop` que ya contiene el PR de Dilan.
4. **Santiago Duarte, un PR:** Docker, cliente, documentación de Fase 3, volumen del registro y reporte de Fase 4. Crear la rama desde el `develop` que ya contiene los PR anteriores.
5. **Integración final:** desde una copia limpia, construir y ejecutar el contenedor, llamar `/health`, enviar una predicción, entrenar una versión, correr pytest y hacer la prueba de monitoreo con dos solicitudes válidas y una inválida.
6. Abrir y revisar un PR de `develop` hacia `main`. Tras fusionarlo, marcar la entrega de las fases 3 y 4 con una etiqueta nueva, sin modificar `entrega-2`.

Los integrantes pueden trabajar en paralelo en archivos separados si acuerdan antes el contrato de la API, el formato del registro y el comando de inicio. Para abrir y fusionar los PR sin conflictos, cada rama debe incorporar el `develop` actualizado y los PR deben integrarse en el orden indicado.

## Lista de aceptación antes de la entrega

### Fase 3

- [ ] `/health` devuelve HTTP 200 y un JSON de estado.
- [ ] `/predict` devuelve predicción y versión para una entrada válida; si falta una variable, indica cuál y responde 400 o 422.
- [ ] Tipos incompatibles y modelo ausente producen errores comprensibles (400/422 y 503, respectivamente).
- [ ] `/train` guarda una versión nueva con modelo, métricas y metadatos sin sobrescribir las anteriores.
- [ ] Pasan las tres pruebas pytest y queda documentada la comprobación manual de `/train`.
- [ ] El cliente de ejemplo funciona contra el contenedor y README muestra una solicitud y respuesta reales.

### Fase 4

- [ ] Cada intento de `/predict`, incluido el rechazado, genera una fila con los campos acordados; no se duplica ni se pierde entre reinicios.
- [ ] El monitor calcula total y porcentaje 4xx/5xx; un registro vacío produce total 0 y “sin solicitudes”.
- [ ] Dos solicitudes válidas y una inválida producen tres filas y 33,3 % de fallos.
- [ ] El reporte contiene los resultados reales, la política de reentrenamiento, dos versiones y cómo seleccionar la anterior.
- [ ] Otra persona puede reconstruir el contenedor y repetir la demostración siguiendo el README.

## Fechas y alcance opcional

Las especificaciones no fijan fechas límite. El despliegue en la nube, los tableros gráficos y el reentrenamiento automático son opcionales; el equipo acuerda las fechas con base en el orden anterior.

## Fuentes

- Evaluación y retroalimentación de Fase 2: `G16_Dilan_Holguin_Evaluacion_Fase_2.docx`.
- Especificaciones técnicas de Fases 3 y 4: `Especificaciones_tecnicas_fases_3_y_4.pdf`.
