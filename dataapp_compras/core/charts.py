# -*- coding: utf-8 -*-
"""
Funções de geração de gráficos (Plotly), reutilizadas pelas abas da
interface para manter os componentes visuais padronizados.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def grafico_barras(df: pd.DataFrame, x: str, y: str, titulo: str, cor=None):
    """Cria um gráfico de barras padronizado usando Plotly Express."""
    if df.empty:
        st.info(f"Dados insuficientes para gerar: {titulo}")
        return
    fig = px.bar(df, x=x, y=y, title=titulo, text_auto=".2s", color=cor)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def grafico_pizza(df: pd.DataFrame, nomes: str, valores: str, titulo: str):
    """Cria um gráfico de pizza padronizado usando Plotly Express."""
    if df.empty:
        st.info(f"Dados insuficientes para gerar: {titulo}")
        return
    fig = px.pie(df, names=nomes, values=valores, title=titulo)
    fig.update_traces(textinfo="label+percent", textposition="inside")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def grafico_linha(df: pd.DataFrame, x: str, y: str, titulo: str):
    """Cria um gráfico de linhas padronizado usando Plotly Express."""
    if df.empty:
        st.info(f"Dados insuficientes para gerar: {titulo}")
        return
    fig = px.line(df, x=x, y=y, title=titulo, markers=True, text=y)
    fig.update_traces(texttemplate="%{y:.2s}", textposition="top center")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

def grafico_curva_abc(df_classificado: pd.DataFrame, titulo: str):
    """
    Gráfico de rosca mostrando a participação percentual de cada classe
    (A, B, C) no total da métrica analisada.
    """
    if df_classificado.empty:
        st.info(f"Dados insuficientes para gerar: {titulo}")
        return
    resumo = (
        df_classificado.groupby("classe")["percentual"]
        .sum()
        .reindex(["A", "B", "C"])
        .fillna(0)
        .reset_index()
    )
    fig = px.pie(
        resumo, names="classe", values="percentual", title=titulo,
        color="classe",
        color_discrete_map={"A": "#2ca02c", "B": "#ff7f0e", "C": "#d62728"},
        hole=0.4,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
