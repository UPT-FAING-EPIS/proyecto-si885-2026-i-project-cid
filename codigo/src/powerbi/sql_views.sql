-- ====================================================================
-- VISTAS SQL PARA CONSUMO DIRECTO EN POWER BI DESKTOP
-- Base de Datos: bi_epis_upt.db (SQLite)
-- ====================================================================

-- 1. Vista Operacional: Resumen General
CREATE VIEW IF NOT EXISTS vw_powerbi_resumen AS
SELECT 
    t.año,
    t.mes,
    t.nombre_mes,
    t.trimestre,
    c.nombre_categoria,
    tc.nombre_tipo AS tipo_contenido,
    rs.nombre_red AS red_social,
    COUNT(h.id_publicacion) AS total_publicaciones,
    SUM(h.likes) AS total_likes,
    SUM(h.comentarios) AS total_comentarios,
    SUM(h.alcance) AS total_alcance,
    SUM(h.engagement) AS total_engagement,
    ROUND(AVG(h.engagement), 2) AS engagement_promedio
FROM hecho_publicacion h
JOIN dim_tiempo t ON h.id_tiempo = t.id_tiempo
JOIN dim_categoria c ON h.id_categoria = c.id_categoria
JOIN dim_tipo_contenido tc ON h.id_tipo_contenido = tc.id_tipo_contenido
JOIN dim_red_social rs ON h.id_red_social = rs.id_red_social
GROUP BY t.año, t.mes, t.nombre_mes, t.trimestre, c.nombre_categoria, tc.nombre_tipo, rs.nombre_red;

-- 2. Vista Táctica: Catálogo / Biblioteca de Publicaciones
CREATE VIEW IF NOT EXISTS vw_powerbi_biblioteca AS
SELECT 
    h.id_publicacion,
    h.codigo_publicacion,
    t.fecha,
    t.año,
    t.mes,
    t.nombre_mes,
    t.semana,
    c.nombre_categoria,
    tc.nombre_tipo AS tipo_contenido,
    rs.nombre_red AS red_social,
    h.likes,
    h.comentarios,
    h.alcance,
    h.engagement,
    h.texto_publicacion,
    h.url_publicacion
FROM hecho_publicacion h
JOIN dim_tiempo t ON h.id_tiempo = t.id_tiempo
JOIN dim_categoria c ON h.id_categoria = c.id_categoria
JOIN dim_tipo_contenido tc ON h.id_tipo_contenido = tc.id_tipo_contenido
JOIN dim_red_social rs ON h.id_red_social = rs.id_red_social;

-- 3. Vista Estratégica: Tendencias Mensuales y Categorías
CREATE VIEW IF NOT EXISTS vw_powerbi_tendencias AS
SELECT 
    t.fecha,
    t.año,
    t.mes,
    t.nombre_mes,
    c.nombre_categoria,
    tc.nombre_tipo AS tipo_contenido,
    h.likes,
    h.comentarios,
    h.engagement,
    h.alcance
FROM hecho_publicacion h
JOIN dim_tiempo t ON h.id_tiempo = t.id_tiempo
JOIN dim_categoria c ON h.id_categoria = c.id_categoria
JOIN dim_tipo_contenido tc ON h.id_tipo_contenido = tc.id_tipo_contenido;
