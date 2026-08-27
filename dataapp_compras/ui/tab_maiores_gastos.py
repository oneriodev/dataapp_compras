# -*- coding: utf-8 -*-
"""
Aba "Maiores Gastos": comparação dos produtos com maior custo líquido
e das marcas com maior valor de impostos.
"""

import streamlit as st

from core.charts import grafico_barras, grafico_linha
from core.metrics import top_n_por_metrica


def aba_maiores_gastos():
    """
    Renderiza a aba com:
    - Gráfico de barras verticais: produtos com maior custo líquido
    - Gráfico de linhas: marcas com maiores impostos
    """
    df = st.session_state["working_df"]
    mapping = st.session_state["column_mapping"]

    if df is None or df.empty:
        st.info("⬅️ Envie um arquivo na barra lateral para iniciar a análise.")
        return

    faltantes = [
        nome for nome, chave in [("Custo Líquido", "custo_liquido"), ("Imposto", "imposto")]
        if not mapping.get(chave)
    ]
    if faltantes:
        st.warning(f"⚠️ Mapeie a(s) coluna(s) de {', '.join(faltantes)} na barra lateral para visualizar os indicadores desta aba.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Produtos com Maior Custo Líquido")
        if mapping.get("custo_liquido"):
            top_custo_liquido = top_n_por_metrica(df, mapping.get("produto"), mapping.get("custo_liquido"))
            grafico_barras(
                top_custo_liquido, x=mapping.get("produto"), y=mapping.get("custo_liquido"),
                titulo="Top 5 Produtos por Custo Líquido",
            )
        else:
            st.info("Mapeie a coluna de 'Custo Líquido' na barra lateral.")

    with col2:
        st.subheader("📈 Marcas com Maiores Impostos")
        if mapping.get("imposto"):
            top_imposto = top_n_por_metrica(df, mapping.get("marca"), mapping.get("imposto"))
            grafico_linha(
                top_imposto, x=mapping.get("marca"), y=mapping.get("imposto"),
                titulo="Top 5 Marcas por Imposto",
            )
        else:
            st.info("Mapeie a coluna de 'Imposto' na barra lateral.")