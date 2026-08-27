# -*- coding: utf-8 -*-
"""
Aba "Produtos / Visão Geral": KPIs, rankings de vendas e lucratividade.
"""

import pandas as pd
import streamlit as st

from core.charts import grafico_barras, grafico_curva_abc, grafico_pizza
from core.metrics import calcular_curva_abc, compute_kpis, listar_margem_negativa, top_n_por_metrica

def aba_produtos_visao_geral():
    """
    Renderiza a aba principal com:
    - KPIs gerais (faturamento, lucro, média/total de vendas, margem)
    - Top 5 produtos e marcas em vendas
    - Produtos e marcas mais lucrativos
    - Curva ABC de produtos/marcas e produtos com margem negativa
    """
    df = st.session_state["working_df"]
    mapping = st.session_state["column_mapping"]

    if df is None or df.empty:
        st.info("⬅️ Envie um arquivo na barra lateral para iniciar a análise.")
        return

    if not mapping.get("faturamento"):
        st.warning(
            "⚠️ Configure o mapeamento de colunas na barra lateral "
            "(ao menos 'Produto' e 'Faturamento') para visualizar os indicadores."
        )

    # ---- KPIs ----
    st.subheader("📊 Indicadores Gerais")
    kpis = compute_kpis(df, mapping)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Faturamento Total", f"R$ {kpis['faturamento_total']:,.2f}")
    c2.metric(
        "Lucro",
        f"R$ {kpis['lucro_total']:,.2f}" if not pd.isna(kpis["lucro_total"]) else "N/D",
    )
    c3.metric(
        "Margem",
        f"{kpis['margem']:.1f}%" if not pd.isna(kpis["margem"]) else "N/D",
    )
    c4.metric("Total de Vendas", f"{kpis['total_vendas']:,.0f}")
    c5.metric(
        "Média de Vendas",
        f"{kpis['media_vendas']:,.2f}" if not pd.isna(kpis["media_vendas"]) else "N/D",
    )

    # ---- Margem Bruta vs. Margem sobre Custo Líquido ----
    if mapping.get("custo_liquido") and not pd.isna(kpis["margem_liquida"]):
        st.caption("📊 Comparativo de Margem: Custo Bruto vs. Custo Líquido")
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric(
            "Margem Bruta",
            f"{kpis['margem']:.1f}%" if not pd.isna(kpis["margem"]) else "N/D",
            help="Faturamento menos Custo Bruto, dividido pelo Faturamento.",
        )
        cm2.metric(
            "Margem s/ Custo Líquido",
            f"{kpis['margem_liquida']:.1f}%",
            help="Faturamento menos Custo Líquido (já considera impostos/descontos do ERP), dividido pelo Faturamento.",
        )
        diferenca = kpis["margem_liquida"] - kpis["margem"]
        cm3.metric(
            "Diferença",
            f"{diferenca:+.1f} p.p.",
            help="Quanto a margem melhora (ou piora) ao considerar o Custo Líquido em vez do Custo Bruto.",
        )

    st.divider()

    # ---- Top produtos e marcas em vendas ----
    st.subheader("🏆 Rankings de Vendas")
    col1, col2 = st.columns(2)
    with col1:
        top_produtos_vendas = top_n_por_metrica(df, mapping.get("produto"), mapping.get("quantidade"))
        grafico_barras(
            top_produtos_vendas, x=mapping.get("produto"), y=mapping.get("quantidade"),
            titulo="Top 5 Produtos em Vendas",
        )
    with col2:
        top_marcas_vendas = top_n_por_metrica(df, mapping.get("marca"), mapping.get("quantidade"))
        grafico_barras(
            top_marcas_vendas, x=mapping.get("marca"), y=mapping.get("quantidade"),
            titulo="Top 5 Marcas em Vendas",
        )

    # ---- Produtos e marcas mais lucrativos ----
    st.subheader("💰 Rankings de Lucratividade")
    if mapping.get("faturamento") and mapping.get("custo"):
        df_lucro = df.copy()
        df_lucro["__lucro__"] = df_lucro[mapping["faturamento"]] - df_lucro[mapping["custo"]]

        col3, col4 = st.columns(2)
        with col3:
            top_produtos_lucro = top_n_por_metrica(df_lucro, mapping.get("produto"), "__lucro__")
            top_produtos_lucro = top_produtos_lucro.rename(columns={"__lucro__": "Lucro"})
            grafico_barras(
                top_produtos_lucro, x=mapping.get("produto"), y="Lucro",
                titulo="Produtos Mais Lucrativos",
            )
        with col4:
            top_marcas_lucro = top_n_por_metrica(df_lucro, mapping.get("marca"), "__lucro__")
            top_marcas_lucro = top_marcas_lucro.rename(columns={"__lucro__": "Lucro"})
            grafico_pizza(
                top_marcas_lucro, nomes=mapping.get("marca"), valores="Lucro",
                titulo="Marcas Mais Lucrativas",
            )
    else:
        st.info("Mapeie as colunas de 'Faturamento' e 'Custo' para ver a lucratividade.")

    # ---- Curva ABC ----
    st.subheader("📐 Curva ABC")
    if mapping.get("faturamento") and (mapping.get("marca") or mapping.get("produto")):
        agrupador_escolhido = st.radio(
            "Classificar por:", ["Marca", "Produto"], horizontal=True, key="curva_abc_agrupador"
        )
        col_agrupador = mapping.get("marca") if agrupador_escolhido == "Marca" else mapping.get("produto")

        if col_agrupador:
            curva = calcular_curva_abc(df, col_agrupador, mapping["faturamento"])
            col5, col6 = st.columns([1, 2])
            with col5:
                grafico_curva_abc(curva, f"Distribuição de Faturamento por Classe ({agrupador_escolhido})")
            with col6:
                if not curva.empty:
                    st.caption(f"Itens classe A (até 80% do faturamento) — {agrupador_escolhido}")
                    st.dataframe(
                        curva[curva["classe"] == "A"][[col_agrupador, "percentual", "percentual_acumulado"]],
                        use_container_width=True,
                        hide_index=True,
                    )
        else:
            st.info(f"Mapeie a coluna de '{agrupador_escolhido}' para calcular a curva ABC.")
    else:
        st.info("Mapeie 'Faturamento' e ao menos 'Produto' ou 'Marca' para calcular a curva ABC.")

    # ---- Produtos com margem negativa ----
    st.subheader("🚨 Produtos com Margem Negativa")
    if mapping.get("produto") and mapping.get("faturamento") and mapping.get("custo"):
        margem_negativa = listar_margem_negativa(df, mapping)
        if margem_negativa.empty:
            st.success("Nenhum produto com margem negativa encontrado nos dados selecionados.")
        else:
            grafico_barras(
                margem_negativa, x=mapping["produto"], y="lucro",
                titulo="Produtos Vendidos Abaixo do Custo (prejuízo)",
            )
    else:
        st.info("Mapeie 'Produto', 'Faturamento' e 'Custo' para identificar itens com margem negativa.")