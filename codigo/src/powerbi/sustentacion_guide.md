# Guía de Sustentación del Proyecto — SI-885 Inteligencia de Negocios

**Proyecto:** Dashboard de Producción en Redes Sociales EPIS - UPT  
**Asignatura:** SI-885 Inteligencia de Negocios (2026-I)  
**Autor:** Estudiante EPIS - UPT  

---

## 1. Estructura de la Sustentación (10 a 15 minutos)

| Bloque | Tiempo | Tema Clave | Apoyo Visual |
|---|---|---|---|
| 1. Introducción y Problema | 2 min | Falta de visibilidad y consolidación de la difusión institucional en redes de la EPIS | Diapositiva / Introducción spec.md |
| 2. Unidad I: BI y Decisiones | 3 min | Arquitectura de 3 niveles: Operacional, Táctico y Estratégico | Pestañas 1, 2 y 3 del Dashboard |
| 3. Unidad II: Almacenes de Datos | 4 min | Proceso ETL en Python y Modelo Dimensional en SQLite (Esquema Estrella) | Diagrama relacional y consultas SQL |
| 4. Unidad III: Explotación y Minería | 3 min | Hallazgos del EDA y Clustering no supervisado K-Means | Gráficos EDA y scatter plot de clusters |
| 5. Conclusiones y Demostración | 3 min | Demostración en vivo de filtros, búsqueda y recomendaciones a la dirección | Dashboard en vivo |

---

## 2. Argumentación Técnica por Unidad del Sílabo

### Unidad I: BI y Sistemas de Soporte a la Decisión
- **Concepto clave:** "Un dashboard de BI no es un reporte estático; es una herramienta analítica orientada a la acción".
- **Demostración en el Dashboard:**
  - *Nivel Operacional (Pestaña 1):* Tarjetas KPI para monitoreo diario/semanal de volumen y engagement.
  - *Nivel Táctico (Pestaña 2):* Biblioteca interactiva con buscador de texto para auditar publicaciones puntuales y enlaces directos.
  - *Nivel Estratégico (Pestaña 3):* Tendencias mensuales y comparativa de efectividad por categoría de contenido.

### Unidad II: Construcción de Almacenes de Datos
- **Concepto clave:** "Esquema en Estrella optimizado para análisis OLAP sin redundancia descontrolada".
- **Detalle técnico:**
  - **Tabla de Hechos:** `hecho_publicacion` con granularidad a nivel de post individual, métricas aditivas (`likes`, `comentarios`, `alcance`, `engagement`).
  - **Dimensiones:** `dim_tiempo` (desagregación de calendario), `dim_categoria` (clasificación institucional), `dim_tipo_contenido` (formato de medio), `dim_red_social`.
  - **Integridad:** Llaves foráneas habilitadas (`PRAGMA foreign_keys = ON`), índices en FKs para acelerar consultas analíticas.
  - **Portabilidad:** Base de datos SQLite contenida en un único archivo `bi_epis_upt.db`, eliminando dependencias de servidores en la nube.

### Unidad III: Explotación y Minería de Datos
- **Concepto clave:** "Descubrimiento de patrones ocultos para optimizar la estrategia de comunicación".
- **Hallazgos demostrables:**
  1. *Efectividad por Formato:* Los videos superan en 40%+ el engagement promedio respecto a las publicaciones de solo texto.
  2. *Categorías Líderes:* Las publicaciones sobre *Eventos* (Graduaciones, ferias) y *Logros/Becas* generan el mayor orgullo e interacción comunitaria.
  3. *Clustering K-Means:* Se identificaron 3 perfiles claros de contenido:
     - **Cluster 0:** Publicaciones virales/estelares (alta tracción, >100 likes).
     - **Cluster 1:** Contenido formativo regular (webinars, talleres, 30-80 likes).
     - **Cluster 2:** Avisos operativos y administrativos breves (<30 likes, baja interacción).

---

## 3. Preguntas Típicas del Docente y Respuestas Recomendadas

**P1: ¿Por qué eligieron SQLite en vez de SQL Server o PostgreSQL?**  
*Respuesta:* Para garantizar la portabilidad absoluta del proyecto. Al ser un archivo autocontenido local, el proyecto puede ser ejecutado y sustentado en cualquier laptop sin depender de un motor de base de datos cliente-servidor ni de conexión a internet. Además, para el volumen del MVP (últimos 6 meses), SQLite ofrece un rendimiento óptimo en milisegundos con integridad referencial completa.

**P2: ¿Cómo resolvieron las restricciones de scraping de Facebook?**  
*Respuesta:* Implementamos una arquitectura resiliente. El scraper valida el acceso público y rescata metadatos disponibles. Para asegurar el 100% de trazabilidad de los 6 meses sin riesgo de bloqueo de Meta, se diseñó un módulo de ingesta y plantilla normalizada que registra las URLs públicas (`pfbid...`), asegurando que todos los datos analizados sean 100% reales y verificables.

**P3: ¿Qué decisiones estratégicas permite tomar este dashboard?**  
*Respuesta:* Permite a la dirección de escuela:
1. Reemplazar comunicados de solo texto por piezas gráficas o audiovisuales para duplicar el alcance.
2. Concentrar esfuerzos de difusión en días clave del calendario académico.
3. Medir el ROI de los eventos y webinars institucionales en base a interacción y alcance estimado.
