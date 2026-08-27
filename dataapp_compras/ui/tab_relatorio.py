# -*- coding: utf-8 -*-
"""
Aba "Relatório": gera uma síntese textual objetiva dos principais
achados da análise (visão geral, concentração de faturamento, itens
com margem negativa, carga tributária), com recomendações de ação
para cada ponto relevante.
"""

import streamlit as st

from core.insights import gerar_insights

_RENDER_NIVEL = {
    "critico": st.error,
    "alerta": st.warning,
    "info": st.info,
    "positivo": st.success,
}


def aba_relatorio():
    """
    Renderiza a aba de relatório: botão "Gerar relatório" que sintetiza
    os achados das demais abas (Produtos / Visão Geral e Maiores Gastos)
    em texto direto, com recomendação de ação por ponto relevante.
    """
    df = st.session_state["working_df"]
    mapping = st.session_state["column_mapping"]

    if df is None or df.empty:
        st.info("⬅️ Envie um arquivo na barra lateral para gerar o relatório.")
        return

    st.subheader("📋 Relatório de Insights")
    st.caption("Síntese objetiva dos principais achados, com recomendações de ação.")

    if st.button("📝 Gerar relatório", type="primary", use_container_width=True):
        insights = gerar_insights(df, mapping)
        if not insights:
            st.warning(
                "Não há dados suficientes mapeados para gerar o relatório. "
                "Confira o mapeamento de colunas na barra lateral."
            )
            st.session_state["ultimo_relatorio"] = None
        else:
            st.session_state["ultimo_relatorio"] = insights

    insights = st.session_state.get("ultimo_relatorio")
    if not insights:
        return

    for insight in insights:
        render_fn = _RENDER_NIVEL.get(insight["nivel"], st.info)
        render_fn(f"**{insight['titulo']}**\n\n{insight['texto']}")

    texto_completo = "\n\n".join(
        f"{insight['titulo'].upper()}\n{insight['texto']}" for insight in insights
    )
    st.download_button(
        "⬇️ Baixar relatório (texto)",
        data=texto_completo.encode("utf-8"),
        file_name="relatorio_insights.txt",
        mime="text/plain",
    )