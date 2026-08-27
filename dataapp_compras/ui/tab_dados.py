# -*- coding: utf-8 -*-
"""
Aba "Dados": visualização tabular dos dados selecionados para a análise,
com opção de exportação em CSV.
"""

import streamlit as st


def aba_dados():
    """
    Renderiza uma visualização tabular dos dados após a modelagem
    (colunas selecionadas pelo usuário), útil para conferência.
    """
    df = st.session_state["working_df"]
    if df is None or df.empty:
        st.info("⬅️ Envie um arquivo na barra lateral para visualizar os dados.")
        return

    st.subheader("🗂️ Dados Selecionados para Análise")
    st.caption(f"Fonte: {st.session_state.get('data_loaded_from', 'desconhecida')} | {len(df)} linhas")
    st.dataframe(df, use_container_width=True)

    # Exportação dos dados tratados
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Baixar dados tratados (CSV)",
        data=csv_bytes,
        file_name="dados_tratados.csv",
        mime="text/csv",
    )
