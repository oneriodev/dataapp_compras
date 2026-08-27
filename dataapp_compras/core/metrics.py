# -*- coding: utf-8 -*-
"""
Funções de métricas e cálculos.

Toda a lógica de negócio (KPIs, rankings Top N)
fica isolada aqui, sem nenhuma dependência do Streamlit — o que também
facilita testar essas funções isoladamente.
"""

import numpy as np
import pandas as pd


def compute_kpis(df: pd.DataFrame, mapping: dict) -> dict:
    col_valor = mapping.get("faturamento")
    col_custo = mapping.get("custo")
    col_custo_liquido = mapping.get("custo_liquido")
    col_qtd = mapping.get("quantidade")

    faturamento_total = df[col_valor].sum() if col_valor else 0
    custo_total = df[col_custo].sum() if col_custo else 0
    lucro_total = faturamento_total - custo_total if col_custo else np.nan
    margem = (lucro_total / faturamento_total * 100) if (col_custo and faturamento_total) else np.nan
    total_vendas = df[col_qtd].sum() if col_qtd else len(df)
    media_vendas = df[col_qtd].mean() if col_qtd else np.nan

    custo_liquido_total = df[col_custo_liquido].sum() if col_custo_liquido else np.nan
    margem_liquida = (
        ((faturamento_total - custo_liquido_total) / faturamento_total * 100)
        if (col_custo_liquido and faturamento_total) else np.nan
    )

    return {
        "faturamento_total": faturamento_total,
        "custo_total": custo_total,
        "lucro_total": lucro_total,
        "margem": margem,
        "total_vendas": total_vendas,
        "media_vendas": media_vendas,
        "margem_liquida": margem_liquida,
    }


def top_n_por_metrica(df: pd.DataFrame, agrupador: str, metrica: str, n: int = 5) -> pd.DataFrame:
    """
    Agrupa o DataFrame por uma coluna categórica (produto ou marca) e retorna
    o Top N com base na soma de uma métrica numérica (vendas, faturamento, lucro).
    """
    if agrupador not in df.columns or metrica not in df.columns:
        return pd.DataFrame()
    resultado = (
        df.groupby(agrupador, dropna=True)[metrica]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )
    return resultado

def calcular_curva_abc(df: pd.DataFrame, agrupador: str, metrica: str,
                        corte_a: float = 80.0, corte_b: float = 95.0) -> pd.DataFrame:
    """
    Classifica itens (produtos ou marcas) em curva ABC com base na
    participação acumulada em uma métrica (normalmente faturamento).
    Classe A: itens que, somados, representam até `corte_a`% do total.
    Classe B: de `corte_a`% até `corte_b`%.
    Classe C: os demais, até 100%.
    """
    if not agrupador or not metrica:
        return pd.DataFrame()
    if agrupador not in df.columns or metrica not in df.columns:
        return pd.DataFrame()

    agrupado = (
        df.groupby(agrupador, dropna=True)[metrica]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    total = agrupado[metrica].sum()
    if total == 0:
        return pd.DataFrame()

    agrupado["percentual"] = agrupado[metrica] / total * 100
    agrupado["percentual_acumulado"] = agrupado["percentual"].cumsum()

    def classificar(pct_acum):
        if pct_acum <= corte_a:
            return "A"
        elif pct_acum <= corte_b:
            return "B"
        return "C"

    agrupado["classe"] = agrupado["percentual_acumulado"].apply(classificar)
    return agrupado


def listar_margem_negativa(df: pd.DataFrame, mapping: dict, n: int = 10) -> pd.DataFrame:
    """
    Lista os itens (produto, conforme mapeamento) vendidos com margem
    negativa — faturamento abaixo do custo. Ordenado do pior prejuízo
    para o menor.
    """
    col_produto = mapping.get("produto")
    col_faturamento = mapping.get("faturamento")
    col_custo = mapping.get("custo")

    if not (col_produto and col_faturamento and col_custo):
        return pd.DataFrame()
    if col_produto not in df.columns or col_faturamento not in df.columns or col_custo not in df.columns:
        return pd.DataFrame()

    agrupado = (
        df.groupby(col_produto, dropna=True)[[col_faturamento, col_custo]]
        .sum()
        .reset_index()
    )
    agrupado["lucro"] = agrupado[col_faturamento] - agrupado[col_custo]
    agrupado["margem_pct"] = np.where(
        agrupado[col_faturamento] > 0,
        agrupado["lucro"] / agrupado[col_faturamento] * 100,
        0,
    )
    negativos = agrupado[agrupado["lucro"] < 0].sort_values("lucro").head(n)
    return negativos
