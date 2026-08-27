# -*- coding: utf-8 -*-
"""
Barra lateral: importação de dados, modelagem (seleção/exclusão de
colunas e mapeamento de papéis) e ações de salvar/resetar.
"""

import streamlit as st

from core.data_loader import auto_suggest_column_mapping, load_uploaded_file
from core.database import clear_db, load_dataframe_from_db, save_dataframe_to_db
from core.state import reset_analysis


def sidebar_importacao_e_modelagem():
    """
    Constrói a barra lateral com:
    - Upload de arquivo (CSV/XLSX)
    - Seleção/exclusão de colunas
    - Mapeamento de papéis das colunas (necessário para os cálculos)
    - Botões de salvar no banco e resetar análise
    """
    st.sidebar.header("📥 Importação de Dados")

    uploaded_file = st.sidebar.file_uploader(
        "Envie um arquivo CSV ou XLSX", type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None and st.session_state["raw_df"] is None:
        try:
            df = load_uploaded_file(uploaded_file)
            st.session_state["raw_df"] = df
            st.session_state["working_df"] = df.copy()
            st.session_state["data_loaded_from"] = uploaded_file.name
            st.session_state["column_mapping"] = auto_suggest_column_mapping(list(df.columns))
            st.sidebar.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")
        except Exception as e:
            st.sidebar.error(f"Erro ao carregar arquivo: {e}")

    # Opção de carregar dados já salvos no banco local
    if st.session_state["raw_df"] is None:
        if st.sidebar.button("📂 Carregar última análise salva no banco"):
            df_banco = load_dataframe_from_db()
            if not df_banco.empty:
                st.session_state["raw_df"] = df_banco
                st.session_state["working_df"] = df_banco.copy()
                st.session_state["data_loaded_from"] = "Banco de dados local"
                st.session_state["column_mapping"] = auto_suggest_column_mapping(list(df_banco.columns))
                st.sidebar.success("Dados carregados do banco local.")
            else:
                st.sidebar.warning("Nenhum dado salvo encontrado no banco.")

    st.sidebar.divider()

    if st.session_state["raw_df"] is not None:
        st.sidebar.header("🧩 Modelagem da Análise")

        todas_colunas = list(st.session_state["raw_df"].columns)
        colunas_selecionadas = st.sidebar.multiselect(
            "Selecione as colunas que deseja usar na análise",
            options=todas_colunas,
            default=list(st.session_state["working_df"].columns)
            if st.session_state["working_df"] is not None
            else todas_colunas,
        )

        if colunas_selecionadas:
            st.session_state["working_df"] = st.session_state["raw_df"][colunas_selecionadas].copy()
        else:
            st.sidebar.warning("Selecione ao menos uma coluna.")

        st.sidebar.subheader("Mapeamento de campos")
        st.sidebar.caption(
            "Indique qual coluna representa cada informação. "
            "Isso é necessário para calcular corretamente as métricas."
        )

        colunas_atuais = list(st.session_state["working_df"].columns) if st.session_state["working_df"] is not None else []
        opcoes = ["(nenhuma)"] + colunas_atuais

        def selectbox_mapeamento(label, chave):
            valor_atual = st.session_state["column_mapping"].get(chave, "(nenhuma)")
            index = opcoes.index(valor_atual) if valor_atual in opcoes else 0
            escolha = st.sidebar.selectbox(label, opcoes, index=index, key=f"map_{chave}")
            st.session_state["column_mapping"][chave] = None if escolha == "(nenhuma)" else escolha

        selectbox_mapeamento("Produto", "produto")
        selectbox_mapeamento("Marca", "marca")
        selectbox_mapeamento("Quantidade vendida", "quantidade")
        selectbox_mapeamento("Faturamento / Valor de venda", "faturamento")
        selectbox_mapeamento("Custo", "custo")
        selectbox_mapeamento("Custo Líquido", "custo_liquido")
        selectbox_mapeamento("Imposto", "imposto")

        st.sidebar.divider()
        col_a, col_b = st.sidebar.columns(2)
        with col_a:
            if st.button("💾 Salvar no banco", use_container_width=True):
                save_dataframe_to_db(st.session_state["working_df"])
                st.sidebar.success("Dados salvos no banco local!")
        with col_b:
            if st.button("🔄 Resetar análise", use_container_width=True):
                clear_db()
                reset_analysis()
                st.rerun()
