"""Seis reportes de producción estudiantil EPIS basados en datos verificables."""

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


def _sum_known(frame: pd.DataFrame, column: str) -> int | None:
    values = frame[column].dropna()
    return int(values.sum()) if len(values) else None


def _group(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return frame.groupby(keys, dropna=False).agg(publicaciones=("id", "count")).reset_index()


def main() -> None:
    st.set_page_config(page_title="Producción social EPIS", layout="wide")
    st.title("Producción en redes sociales de estudiantes EPIS")
    st.caption("Publicaciones verificables de cuentas participantes · métricas de la última captura disponible")
    db = _db_path()
    all_posts = load_posts(db)
    if all_posts.empty:
        st.info("Aún no hay publicaciones verificadas. Importe una exportación autorizada para activar los reportes.")
        st.code("python -m unidad2.pipeline --manifest RUTA_MANIFIESTO --csv RUTA_CSV --db RUTA_BASE")
        st.stop()

    years = sorted(int(x) for x in all_posts["year"].dropna().unique())
    platforms = sorted(str(x) for x in all_posts["platform"].dropna().unique())
    st.sidebar.header("Filtros")
    year = st.sidebar.selectbox("Año", [None, *years], format_func=lambda x: "Todos" if x is None else str(x))
    month = st.sidebar.selectbox("Mes", [None, *range(1, 13)], format_func=lambda x: "Todos" if x is None else f"{x:02d}")
    day = st.sidebar.selectbox("Día", [None, *range(1, 32)], format_func=lambda x: "Todos" if x is None else f"{x:02d}")
    platform = st.sidebar.selectbox("Plataforma", [None, *platforms], format_func=lambda x: x or "Todas")
    posts = filtered(all_posts, year, month, day, platform)
    st.caption(f"{len(posts)} publicaciones dentro del filtro · los valores ausentes no se convierten en cero")
    if posts.empty:
        st.warning("No hay publicaciones para esta combinación de filtros.")
        st.stop()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "1 · Producción temporal", "2 · Plataformas", "3 · Proyectos",
        "4 · Temas y formatos", "5 · Interacciones", "6 · Calidad del dato",
    ])
    with tab1:
        st.subheader("Publicaciones por fecha")
        by_date = _group(posts, ["date_key"]).sort_values("date_key")
        st.bar_chart(by_date.set_index("date_key")["publicaciones"])
        st.dataframe(by_date, hide_index=True, width="stretch")
    with tab2:
        st.subheader("Producción por plataforma")
        by_platform = _group(posts, ["platform"]).sort_values("publicaciones", ascending=False)
        st.bar_chart(by_platform.set_index("platform")["publicaciones"])
        st.dataframe(by_platform, hide_index=True, width="stretch")
    with tab3:
        st.subheader("Proyectos difundidos")
        projects = posts.copy()
        projects["project"] = projects["project"].fillna("Sin proyecto identificado")
        by_project = _group(projects, ["project"]).sort_values("publicaciones", ascending=False)
        st.bar_chart(by_project.set_index("project")["publicaciones"])
        st.dataframe(projects[["project", "platform", "account", "date_key", "post_url"]],
                     hide_index=True, width="stretch", column_config={"post_url": st.column_config.LinkColumn("Publicación original")})
    with tab4:
        st.subheader("Temas y formatos")
        categories = posts.copy()
        categories["topic"] = categories["topic"].replace("", "Sin clasificar").fillna("Sin clasificar")
        categories["content_type"] = categories["content_type"].fillna("Sin clasificar")
        st.dataframe(_group(categories, ["topic", "content_type"]).sort_values("publicaciones", ascending=False),
                     hide_index=True, width="stretch")
        st.bar_chart(_group(categories, ["content_type"]).set_index("content_type")["publicaciones"])
    with tab5:
        st.subheader("Interacciones registradas")
        st.caption("Reacciones, comentarios y compartidos se muestran por separado. No se suman alcance e impresiones entre plataformas.")
        cols = st.columns(3)
        for col, metric, label in zip(cols, ("likes", "comments", "shares"), ("Reacciones", "Comentarios", "Compartidos")):
            result = _sum_known(posts, metric)
            col.metric(label, "Sin datos" if result is None else f"{result:,}")
        st.dataframe(posts[["date_key", "platform", "post_url", "likes", "comments", "shares", "reach", "impressions", "metrics_captured_at"]],
                     hide_index=True, width="stretch", column_config={"post_url": st.column_config.LinkColumn("Publicación original")})
    with tab6:
        st.subheader("Procedencia y calidad")
        q = quality(db)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Lotes importados", q["batches"])
        c2.metric("Publicaciones", q["posts"])
        c3.metric("Capturas de métricas", q["snapshots"])
        c4.metric("Errores de integridad", q["fk_errors"])
        st.caption(f"Última importación: {q['last_import'] or 'ninguna'} · Publicaciones con alguna métrica ausente: {q['missing_metrics']}")
        st.dataframe(posts[["post_url", "account", "source_kind", "source_sha256", "evidence_sha256", "authorization_reference", "public_source_url", "metrics_captured_at"]],
                     hide_index=True, width="stretch", column_config={"post_url": st.column_config.LinkColumn("Fuente")})


if __name__ == "__main__":
    main()
