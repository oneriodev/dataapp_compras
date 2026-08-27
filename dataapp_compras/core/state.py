# -*- coding: utf-8 -*-
"""
Gerenciamento do estado da sessão (st.session_state).

Centraliza a inicialização das chaves usadas pela aplicação e a lógica
de reset da análise atual.
"""

import streamlit as st


def init_session_state():
    defaults = {
        "raw_df": None,
        "working_df": None,
        "column_mapping": {},
        "data_loaded_from": None,
        "ultimo_relatorio": None,  # insights gerados pelo botão "Gerar relatório"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_analysis():
    st.session_state["raw_df"] = None
    st.session_state["working_df"] = None
    st.session_state["column_mapping"] = {}
    st.session_state["data_loaded_from"] = None
    st.session_state["ultimo_relatorio"] = None  # <- adicionar esta linha
    st.success("Análise resetada. Envie um novo arquivo para começar.")