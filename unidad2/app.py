"""Dashboard de producción estudiantil; las cifras se consultan en el almacén."""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from unidad2.reports import filtered, load_posts, quality


def _db_path() -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--db", default=os.environ.get("EPIS_DB_PATH", str(Path(__file__).resolve().parent / "data" / "observatorio.db")))
    args, _ = parser.parse_known_args()
    return Path(args.db)


def _group(frame, keys):
    return frame.groupby(keys, dropna=False).agg(publicaciones=("id", "count")).reset_index()


def _table(frame):
    st.dataframe(frame, hide_index=True, width="stretch", column_config={
        "post_url": st.column_config.LinkColumn("Publicación original"),
        "affiliation_evidence": st.column_config.LinkColumn("Vínculo EPIS"),
        "published_label": "Etiqueta temporal de la primera observación",
        "published_at": "Fecha exacta de publicación",
        "metrics_captured_at": "Fecha de captura",
        "likes": "Reacciones", "comments": "Comentarios", "shares": "Compartidos",
        "reach": "Alcance", "impressions": "Impresiones", "account": "Autor",
        "platform": "Red social", "project": "Proyecto", "topic": "Tema",
        "content_type": "Formato", "source_kind": "Método de obtención",
        "publicaciones": "Publicaciones",
    })


def main():
    st.set_page_config(page_title="EPIS · Producción social", page_icon="📊", layout="wide")
    st.caption("UNIVERSIDAD PRIVADA DE TACNA · INTELIGENCIA DE NEGOCIOS")
    st.title("Producción social EPIS")
    st.write("Qué publican los estudiantes, sobre qué temas y qué respuesta reciben.")
    db = _db_path()
    all_posts = load_posts(db)
    if all_posts.empty:
        st.info("Todavía no hay datos cargados. Los gráficos se activarán con publicaciones y evidencia reales.")
        st.stop()

    st.sidebar.header("Explorar publicaciones")
    basis = st.sidebar.selectbox("Fecha para los filtros", ["capture", "publication"],
                                format_func=lambda x: "Fecha de captura" if x == "capture" else "Fecha de publicación")
    dated = filtered(all_posts, date_basis=basis)
    years = sorted(int(x) for x in dated["year"].dropna().unique())
    year = st.sidebar.selectbox("Año", [None, *years], format_func=lambda x: "Todos" if x is None else str(x))
    month = st.sidebar.selectbox("Mes", [None, *range(1, 13)], format_func=lambda x: "Todos" if x is None else f"{x:02d}")
    day = st.sidebar.selectbox("Día", [None, *range(1, 32)], format_func=lambda x: "Todos" if x is None else f"{x:02d}")
    platforms = sorted(all_posts["platform"].dropna().unique())
    platform = st.sidebar.selectbox("Red social", [None, *platforms], format_func=lambda x: x or "Todas")
    posts = filtered(all_posts, year, month, day, platform, date_basis=basis)
    accounts = sorted(posts["account"].dropna().unique())
    account = st.sidebar.selectbox("Autor", [None, *accounts], format_func=lambda x: x or "Todos")
    if account:
        posts = posts.loc[posts["account"] == account].copy()
    st.sidebar.caption("Zona horaria: Perú (UTC−5). Una fecha relativa no se transforma en un día inventado.")
    st.info("Muestra observada de perfiles con vínculo declarado a EPIS. No representa a toda la escuela ni acredita matrícula vigente.")
    if basis == "capture":
        st.caption("El filtro temporal indica cuándo se observaron los datos, no cuándo se publicaron. Cambia a «Fecha de publicación» para estudiar producción fechada.")
    if posts.empty:
        st.warning("No hay publicaciones con esos filtros y fechas disponibles.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Publicaciones observadas", len(posts))
    c2.metric("Autores", posts["account"].nunique())
    c3.metric("Redes sociales", posts["platform"].nunique())
    c4.metric("Sin fecha exacta de publicación", int(posts["published_at"].isna().sum()))
    st.caption(f"Última captura de esta selección: {posts['metrics_captured_at'].max()}. Los espacios vacíos significan «sin datos».")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "1 · Registro temporal", "2 · Redes sociales", "3 · Autores y proyectos",
        "4 · Temas", "5 · Interacciones", "6 · Calidad y fuentes",
    ])
    with tab1:
        st.subheader("Publicaciones observadas por fecha de captura" if basis == "capture" else "Producción por fecha de publicación")
        dates = posts.dropna(subset=["analysis_date"])
        if not dates.empty:
            st.bar_chart(_group(dates, ["analysis_date"]).sort_values("analysis_date"), x="analysis_date", y="publicaciones", x_label="Fecha", y_label="Publicaciones")
        missing_dates = int(posts["analysis_date"].isna().sum())
        if missing_dates:
            st.warning(f"{missing_dates} publicaciones quedan fuera del gráfico temporal porque su fecha exacta no está disponible.")
        _table(posts[["post_url", "published_at", "published_label", "metrics_captured_at"]])
    with tab2:
        st.subheader("Dónde se publica")
        grouped = _group(posts, ["platform"]).sort_values("publicaciones", ascending=False)
        st.bar_chart(grouped, x="platform", y="publicaciones", x_label="Red social", y_label="Publicaciones")
        _table(grouped)
    with tab3:
        st.subheader("Autores de las publicaciones")
        st.bar_chart(_group(posts, ["account"]), x="account", y="publicaciones", x_label="Autor", y_label="Publicaciones")
        st.caption("Una republicación de contenido ajeno no se atribuye como producción original del estudiante.")
        projects = posts.dropna(subset=["project"])
        if projects.empty:
            st.info("En esta selección no se identificaron proyectos específicos. No se asignaron proyectos por suposición.")
        else:
            _table(projects[["project", "account", "post_url"]])
    with tab4:
        st.subheader("Temas de la producción estudiantil")
        categories = posts.copy()
        categories["topic"] = categories["topic"].replace("", "Sin clasificar").fillna("Sin clasificar")
        categories["content_type"] = categories["content_type"].fillna("Sin formato identificado")
        st.bar_chart(_group(categories, ["topic"]), x="topic", y="publicaciones", x_label="Tema", y_label="Publicaciones")
        st.caption("Los temas son una clasificación analítica del contenido, no una métrica suministrada por la red social.")
        _table(_group(categories, ["topic", "content_type"]))
    with tab5:
        st.subheader("Respuesta a las publicaciones")
        cols = st.columns(3)
        labels = {"likes": "Reacciones", "comments": "Comentarios", "shares": "Compartidos"}
        for col, metric in zip(cols, labels):
            values = posts[metric].dropna()
            col.metric(labels[metric], f"{int(values.sum()):,}" if len(values) else "Sin datos")
            col.caption(f"Dato disponible en {len(values)} de {len(posts)} publicaciones")
        measured = posts.loc[posts[list(labels)].notna().any(axis=1)].copy()
        if measured.empty:
            st.info("La fuente no mostró métricas de interacción.")
        else:
            measured["Publicación"] = measured["external_id"].astype(str)
            st.bar_chart(measured.rename(columns=labels), x="Publicación", y=list(labels.values()), stack=False, y_label="Interacciones observadas")
        st.caption("Última captura disponible de cada post. Las sumas son parciales cuando faltan métricas; no equivalen a interacciones nuevas del periodo.")
        _table(posts[["post_url", "likes", "comments", "shares", "reach", "impressions", "metrics_captured_at"]])
    with tab6:
        st.subheader("Qué conocemos y qué falta")
        metrics = ["likes", "comments", "shares", "reach", "impressions"]
        coverage = pd.DataFrame({"Métrica": ["Reacciones", "Comentarios", "Compartidos", "Alcance", "Impresiones"],
                                 "Con dato": posts[metrics].notna().sum().to_numpy(),
                                 "Sin dato": posts[metrics].isna().sum().to_numpy()})
        st.bar_chart(coverage, x="Métrica", y=["Con dato", "Sin dato"], y_label="Publicaciones")
        _table(posts[["post_url", "account", "source_kind", "affiliation_evidence", "metrics_captured_at"]])
        with st.expander("Auditoría del almacén completo"):
            q = quality(db)
            st.write({"Lotes": q["batches"], "Publicaciones": q["posts"], "Capturas": q["snapshots"], "Errores de integridad": q["fk_errors"], "Última importación": q["last_import"]})
            st.caption("Estos totales son globales. Los hashes permiten detectar cambios de archivo; no certifican por sí solos la veracidad de una fuente.")
            _table(posts[["post_url", "source_sha256", "evidence_sha256"]])
    st.download_button("Descargar selección (CSV)", posts.to_csv(index=False).encode("utf-8-sig"), "publicaciones_epis.csv", "text/csv")


if __name__ == "__main__":
    main()
