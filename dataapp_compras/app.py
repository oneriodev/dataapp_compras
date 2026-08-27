# -*- coding: utf-8 -*-
"""
DataApp - Setor de Compras (Rede de Supermercados)
====================================================
Protótipo em Streamlit para análise de métricas de produtos vendidos.

Este arquivo é apenas o ponto de entrada da aplicação: ele configura a
página e monta a interface (barra lateral + abas), delegando toda a
lógica para os módulos em `core/` (dados, banco, métricas, gráficos) e
`ui/` (componentes de interface). Veja a árvore de pastas no README.

Como rodar:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st

from core.state import init_session_state
from ui.sidebar import sidebar_importacao_e_modelagem
from ui.tab_dados import aba_dados
from ui.tab_maiores_gastos import aba_maiores_gastos
from ui.tab_produtos import aba_produtos_visao_geral
from ui.tab_relatorio import aba_relatorio

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO GERAL DA PÁGINA
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="DataApp Compras - Supermercado",
    page_icon="🛒",
    layout="wide",
)


def main():
    init_session_state()

    st.title("🛒 DataApp - Setor de Compras (Supermercado)")
    st.caption("Análise de métricas de produtos vendidos — protótipo em Streamlit")

    sidebar_importacao_e_modelagem()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Produtos / Visão Geral", "💸 Maiores Gastos", "📋 Relatório", "🗂️ Dados"
    ])
    with tab1:
        aba_produtos_visao_geral()
    with tab2:
        aba_maiores_gastos()
    with tab3:
        aba_relatorio()
    with tab4:
        aba_dados()


if __name__ == "__main__":
    main()