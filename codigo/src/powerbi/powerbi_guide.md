# Guía de Construcción del Dashboard en Power BI Desktop — EPIS-UPT

Esta guía documenta paso a paso la creación del Dashboard de Inteligencia de Negocios en **Power BI Desktop**, cumpliendo exactamente con las especificaciones de [design.md](file:///d:/Codigos/Inteligencia%20de%20negocios/Proyecto/proyecot/datos%20importantes/design%20(1).md) y [spec.md](file:///d:/Codigos/Inteligencia%20de%20negocios/Proyecto/proyecot/datos%20importantes/spec.md).

---

## 1. Conexión y Carga de Datos (100% Portátil y Offline)

Para garantizar que el archivo `.pbix` abra en cualquier computadora el día de la sustentación sin depender de controladores externos ni conexión a internet, se proveen dos opciones:

### Opción A (Recomendada para sustentación): Carpeta de CSVs Procesados
1. Abrir **Power BI Desktop**.
2. Ir a **Obtener datos** > **Texto o CSV**.
3. Cargar los siguientes 5 archivos ubicados en `codigo/data/processed/`:
   - `dim_tiempo.csv`
   - `dim_categoria.csv`
   - `dim_tipo_contenido.csv`
   - `dim_red_social.csv`
   - `hecho_publicacion.csv`
4. En el editor de Power Query, verificar que la primera fila se use como encabezado y hacer clic en **Cerrar y aplicar**.

### Opción B: Conexión Directa SQLite vía ODBC
1. Ir a **Obtener datos** > **ODBC**.
2. Seleccionar DSN de SQLite apuntando a `codigo/data/database/bi_epis_upt.db`.
3. Seleccionar las tablas o las vistas analíticas (`vw_powerbi_resumen`, `vw_powerbi_biblioteca`, `vw_powerbi_tendencias`).

---

## 2. Modelo de Datos (Esquema Estrella)

En la vista de **Modelo** de Power BI, configurar las siguientes relaciones (cardinalidad 1 a varios `1:*`, filtro de dirección única):

```
       dim_tiempo (1) ──────────┐
                                │
    dim_categoria (1) ────► [hecho_publicacion] (★) ◄──── dim_tipo_contenido (1)
                                │
   dim_red_social (1) ──────────┘
```

- `dim_tiempo[id_tiempo]` 1 ── * `hecho_publicacion[id_tiempo]`
- `dim_categoria[id_categoria]` 1 ── * `hecho_publicacion[id_categoria]`
- `dim_tipo_contenido[id_tipo_contenido]` 1 ── * `hecho_publicacion[id_tipo_contenido]`
- `dim_red_social[id_red_social]` 1 ── * `hecho_publicacion[id_red_social]`

---

## 3. Catálogo de Medidas DAX

Crear una nueva tabla de medidas llamada `_Medidas` e incorporar las fórmulas del archivo [dax_measures.dax](file:///d:/Codigos/Inteligencia%20de%20negocios/Proyecto/proyecot/codigo/src/powerbi/dax_measures.dax):
- `Total Publicaciones = COUNTROWS('hecho_publicacion')`
- `Total Likes = SUM('hecho_publicacion'[likes])`
- `Total Comentarios = SUM('hecho_publicacion'[comentarios])`
- `Total Alcance = SUM('hecho_publicacion'[alcance])`
- `Total Engagement = [Total Likes] + [Total Comentarios]`
- `Engagement Promedio = DIVIDE([Total Engagement], [Total Publicaciones], 0)`

---

## 4. Construcción de las 3 Pestañas

### Pestaña 1: Resumen General (Nivel Operacional)
- **Banner Superior:** Título *"EPIS - UPT: Dashboard de Producción en Redes Sociales"* (Fondo Azul UPT `#003366`, texto blanco).
- **Tarjetas KPI (Fila Superior):**
  1. `Total Publicaciones` (Tarjeta)
  2. `Total Likes` (Tarjeta)
  3. `Total Comentarios` (Tarjeta)
  4. `Total Alcance` (Tarjeta)
- **Panel Lateral Izquierdo de Filtros:**
  - Segmentación por `dim_tiempo[fecha]` (rango de fechas).
  - Segmentación por `dim_categoria[nombre_categoria]` (lista vertical / menú).
  - Segmentación por `dim_tipo_contenido[nombre_tipo]` (botones).
- **Gráfico Principal Izquierdo:**
  - Gráfico de Columnas Agrupadas: Eje X = `dim_tiempo[nombre_mes]`, Eje Y = `[Total Publicaciones]`.
  - Color de barras: `#0056b3`.
- **Gráfico Principal Derecho:**
  - Gráfico Circular o de Dona: Leyenda = `dim_tipo_contenido[nombre_tipo]`, Valores = `[Total Publicaciones]`.

### Pestaña 2: Detalle por Publicación (Biblioteca)
- **Propósito:** Navegación tipo catálogo con búsqueda libre.
- **Barra de Búsqueda:** Visual de búsqueda de texto o filtro personalizado sobre `hecho_publicacion[texto_publicacion]`.
- **Filtros Superiores:** Segmentaciones por Categoría, Red Social, Tipo de Contenido y Periodo.
- **Tabla Central:**
  - Columnas:
    1. `dim_tiempo[fecha]` (Fecha)
    2. `dim_categoria[nombre_categoria]` (Categoría)
    3. `dim_tipo_contenido[nombre_tipo]` (Tipo)
    4. `hecho_publicacion[likes]` (Likes)
    5. `hecho_publicacion[comentarios]` (Comentarios)
    6. `hecho_publicacion[alcance]` (Alcance)
    7. `hecho_publicacion[texto_publicacion]` (Descripción)
    8. `hecho_publicacion[url_publicacion]` (Enlace Web)
  - Configuración de `url_publicacion`: En la pestaña de *Herramientas de columnas*, cambiar **Categoría de datos** a **Dirección URL web**. Esto habilita el icono de hipervínculo interactivo.

### Pestaña 3: Tendencias en el Tiempo (Nivel Estratégico)
- **Propósito:** Identificar patrones de crecimiento y categorías con mayor interacción.
- **Gráfico Superior (Tendencia Temporal):**
  - Gráfico de Líneas: Eje X = `dim_tiempo[nombre_mes]`, Eje Y = `[Total Publicaciones]`, Eje Y secundario = `[Total Engagement]`.
- **Gráfico Inferior Izquierdo:**
  - Gráfico de Barras Apiladas: Eje Y = `dim_categoria[nombre_categoria]`, Eje X = `[Total Likes]` y `[Total Comentarios]`.
- **Gráfico Inferior Derecho:**
  - Gráfico de Dispersión: Eje X = `hecho_publicacion[likes]`, Eje Y = `hecho_publicacion[comentarios]`, Tamaño de burbuja = `hecho_publicacion[alcance]`, Leyenda = `dim_tipo_contenido[nombre_tipo]`.

---

## 5. Estilo Visual Institucional (UPT)

- **Azul Primario:** `#003366` (Encabezados y tarjetas KPI principales)
- **Azul Secundario:** `#0056b3` (Barras de gráficos y acentos)
- **Naranja Acento:** `#e67e22` (Comentarios y métricas secundarias)
- **Fondo de Página:** `#f4f6f9`
- **Fondo de Tarjetas:** Blanco `#ffffff` con borde tenue
- **Tipografía:** Segoe UI

---

## 6. Exportación a PDF para el Informe Académico

1. En Power BI Desktop, ir a **Archivo** > **Exportar** > **Exportar a PDF**.
2. El sistema generará un documento PDF con las 3 pestañas renderizadas en alta resolución listas para anexar al informe del curso.
