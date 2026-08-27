# -*- coding: utf-8 -*-
"""
Aba "Maiores Gastos": comparação dos produtos com maior custo líquido
e das marcas com maior valor de impostos.
"""

import streamlit as st

from core.charts import grafico_barras, grafico_linha
from core.metrics import calcular_proporcao_gasto, top_n_por_metrica


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
            st.divider()
    st.subheader("📐 Gastos em Proporção ao Faturamento")
    st.caption(
        "Diferente dos rankings acima (que refletem principalmente volume de vendas), "
        "aqui o percentual revela desproporção real entre custo/imposto e receita — "
        "útil para achar marcas problemáticas mesmo com pouco volume."
    )

    if mapping.get("faturamento") and mapping.get("marca"):
        faturamento_total = df[mapping["faturamento"]].sum()
        limiar_relevancia = faturamento_total * 0.01  # ignora marcas com <1% do faturamento total

        col3, col4 = st.columns(2)
        with col3:
            if mapping.get("custo_liquido"):
                prop_custo = calcular_proporcao_gasto(
                    df, mapping["marca"], mapping["faturamento"], mapping["custo_liquido"],
                    faturamento_minimo=limiar_relevancia,
                ).head(5)
                grafico_barras(
                    prop_custo, x=mapping["marca"], y="percentual_sobre_faturamento",
                    titulo="Marcas com Maior % de Custo Líquido s/ Faturamento",
                )
            else:
                st.info("Mapeie a coluna de 'Custo Líquido' na barra lateral.")
        with col4:
            if mapping.get("imposto"):
                prop_imposto = calcular_proporcao_gasto(
                    df, mapping["marca"], mapping["faturamento"], mapping["imposto"],
                    faturamento_minimo=limiar_relevancia,
                ).head(5)
                grafico_barras(
                    prop_imposto, x=mapping["marca"], y="percentual_sobre_faturamento",
                    titulo="Marcas com Maior % de Imposto s/ Faturamento",
                )
            else:
                st.info("Mapeie a coluna de 'Imposto' na barra lateral.")
    else:
        st.info("Mapeie 'Faturamento' e 'Marca' para ver os gastos em proporção.")