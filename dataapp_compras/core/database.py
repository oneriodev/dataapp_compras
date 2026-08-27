# -*- coding: utf-8 -*-
"""
Banco de dados local (SQLAlchemy + SQLite).

Centraliza a conexão e as operações de leitura/escrita usadas para
persistir os dados tratados entre sessões da aplicação.
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from core.config import DB_PATH, TABLE_NAME


@st.cache_resource(show_spinner=False)
def get_engine():
    """
    Cria (ou reaproveita) a conexão com o banco de dados local SQLite.
    O cache_resource garante que a mesma engine seja reutilizada durante
    a sessão do Streamlit, evitando reabrir conexões desnecessariamente.
    """
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return engine


def save_dataframe_to_db(df: pd.DataFrame, table_name: str = TABLE_NAME) -> None:
    """
    Persiste o DataFrame tratado no banco de dados local (SQLite),
    substituindo qualquer dado anterior da mesma tabela.
    """
    engine = get_engine()
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)


def load_dataframe_from_db(table_name: str = TABLE_NAME) -> pd.DataFrame:
    """
    Consulta o banco de dados local e retorna o DataFrame armazenado.
    Retorna DataFrame vazio caso a tabela ainda não exista.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(f"SELECT * FROM {table_name}"), conn)
        return df
    except Exception:
        return pd.DataFrame()


def clear_db(table_name: str = TABLE_NAME) -> None:
    """Remove a tabela de análise do banco local (usado no botão de reset)."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.commit()
