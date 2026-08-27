# -*- coding: utf-8 -*-
"""
Geração de insights textuais objetivos, sintetizando os principais
achados das análises (KPIs, Curva ABC, Margem Negativa, Maiores Gastos)
em linguagem direta e orientada à decisão.

O foco aqui é SÍNTESE, não repetição: em vez de listar cada número de
cada aba separadamente, cada insight cruza informações relacionadas
(ex: um item que aparece ao mesmo tempo entre os mais vendidos E com
margem negativa vira um único alerta crítico, não dois pontos soltos).
"""

import pandas as pd

from core.metrics import (
    calcular_curva_abc,
    calcular_proporcao_gasto,
    compute_kpis,
    listar_margem_negativa,
    top_n_por_metrica,
)


def _fmt_moeda(valor: float) -> str:
    """Formata um número como moeda brasileira: R$ 1.234,56"""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return f"R$ {texto}"


def gerar_insights(df: pd.DataFrame, mapping: dict) -> list:
    insights = []
    kpis = compute_kpis(df, mapping)

    insights.extend(_insight_visao_geral(kpis))
    insights.extend(_insight_curva_abc(df, mapping))
    insights.extend(_insight_margem_negativa(df, mapping))
    insights.extend(_insight_gastos_proporcionais(df, mapping))  # <- nova linha
    insights.extend(_insight_maiores_gastos(df, mapping))

    return insights


def _insight_visao_geral(kpis: dict) -> list:
    if not kpis.get("faturamento_total"):
        return []

    texto = (
        f"Faturamento total de {_fmt_moeda(kpis['faturamento_total'])}, com lucro bruto de "
        f"{_fmt_moeda(kpis['lucro_total'])} e margem bruta de {kpis['margem']:.1f}%."
    )

    margem_liquida = kpis.get("margem_liquida", float("nan"))
    if not pd.isna(margem_liquida):
        diferenca = margem_liquida - kpis["margem"]
        if abs(diferenca) >= 1.0:
            direcao = "melhora" if diferenca > 0 else "piora"
            texto += (
                f" Ao considerar o Custo Líquido em vez do Custo Bruto, a margem {direcao} "
                f"em {abs(diferenca):.1f} ponto(s) percentual(is), chegando a {margem_liquida:.1f}% — "
                "sinal de que impostos/descontos já embutidos no ERP têm efeito relevante sobre a "
                "rentabilidade real, e a margem bruta isoladamente pode distorcer a leitura."
            )

    return [{"titulo": "Visão Geral", "texto": texto, "nivel": "info"}]


def _insight_curva_abc(df: pd.DataFrame, mapping: dict) -> list:
    col_agrupador = mapping.get("marca") or mapping.get("produto")
    if not (col_agrupador and mapping.get("faturamento")):
        return []

    curva = calcular_curva_abc(df, col_agrupador, mapping["faturamento"])
    if curva.empty:
        return []

    n_a = int((curva["classe"] == "A").sum())
    n_total = len(curva)
    if n_a == 0 or n_total == 0:
        return []

    pct_a = curva.loc[curva["classe"] == "A", "percentual"].sum()
    top_a = curva[curva["classe"] == "A"].head(3)[col_agrupador].tolist()

    texto = (
        f"{n_a} de {n_total} itens ({n_a / n_total * 100:.0f}% da base) concentram "
        f"{pct_a:.0f}% do faturamento (classe A da Curva ABC), liderados por "
        f"{', '.join(str(x) for x in top_a)}."
    )

    concentracao_alta = (n_a / n_total) < 0.15
    if concentracao_alta:
        texto += (
            " Concentração elevada em poucos itens: priorize a relação comercial com esses "
            "fornecedores, mas avalie o risco de dependência — se algum deles faltar ou reajustar "
            "preço, o impacto no faturamento total é desproporcional."
        )
        nivel = "alerta"
    else:
        texto += " Priorize negociação de compra e giro de estoque para esses itens."
        nivel = "info"

    return [{"titulo": "Concentração de Faturamento (Curva ABC)", "texto": texto, "nivel": nivel}]


def _insight_margem_negativa(df: pd.DataFrame, mapping: dict) -> list:
    if not (mapping.get("produto") and mapping.get("faturamento") and mapping.get("custo")):
        return []

    negativos = listar_margem_negativa(df, mapping, n=10_000)
    if negativos.empty:
        return [{
            "titulo": "Margem Negativa",
            "texto": "Nenhum item foi identificado vendendo abaixo do custo nos dados analisados.",
            "nivel": "positivo",
        }]

    col_produto = mapping["produto"]
    prejuizo_total = negativos["lucro"].sum()
    pior = negativos.iloc[0]

    # Cruza com volume de vendas: um item com margem negativa que também
    # está entre os mais vendidos é o ponto mais crítico do relatório,
    # porque o prejuízo cresce junto com o volume vendido.
    texto_critico = ""
    if mapping.get("quantidade"):
        top_vendas = top_n_por_metrica(df, col_produto, mapping["quantidade"], n=10)
        itens_top_vendas = set(top_vendas[col_produto])
        itens_criticos = [
            row[col_produto] for _, row in negativos.iterrows()
            if row[col_produto] in itens_top_vendas
        ]
        if itens_criticos:
            texto_critico = (
                f" Atenção especial para {', '.join(str(x) for x in itens_criticos)}: "
                "está entre os itens mais vendidos e, ao mesmo tempo, com margem negativa — "
                "quanto maior o volume vendido, maior o prejuízo acumulado. Priorize a revisão "
                "de preço ou custo desse item antes dos demais."
            )

    texto = (
        f"{len(negativos)} item(ns) vendido(s) abaixo do custo, somando prejuízo de "
        f"{_fmt_moeda(abs(prejuizo_total))}. O maior prejuízo individual é de "
        f"{pior[col_produto]} ({_fmt_moeda(abs(pior['lucro']))})."
        + texto_critico
    )

    nivel = "critico" if texto_critico else "alerta"
    return [{"titulo": "Produtos com Margem Negativa", "texto": texto, "nivel": nivel}]


def _insight_maiores_gastos(df: pd.DataFrame, mapping: dict) -> list:
    if not (mapping.get("imposto") and mapping.get("marca")):
        return []

    top_imposto = top_n_por_metrica(df, mapping["marca"], mapping["imposto"], n=3)
    if top_imposto.empty:
        return []

    nomes = top_imposto[mapping["marca"]].tolist()
    texto = (
        f"As marcas com maior carga de impostos são {', '.join(str(x) for x in nomes)}. "
        "Vale avaliar se essa carga está sendo considerada na precificação dessas marcas — "
        "especialmente se alguma delas também aparecer entre os itens de menor margem."
    )
    return [{"titulo": "Carga Tributária por Marca", "texto": texto, "nivel": "info"}]

def _insight_gastos_proporcionais(df: pd.DataFrame, mapping: dict) -> list:
    """
    Identifica marcas cujo Custo Líquido representa uma fatia
    desproporcional do faturamento — diferente do total absoluto (que
    reflete volume), aqui uma marca pequena com preço mal calibrado
    aparece com o mesmo destaque que uma marca grande.
    """
    if not (mapping.get("marca") and mapping.get("faturamento") and mapping.get("custo_liquido")):
        return []

    faturamento_total = df[mapping["faturamento"]].sum()
    if not faturamento_total:
        return []

    # Ignora marcas com faturamento irrelevante (<1% do total), que
    # distorcem o percentual por amostra pequena sem significar
    # problema real de precificação.
    limiar_relevancia = faturamento_total * 0.01
    prop = calcular_proporcao_gasto(
        df, mapping["marca"], mapping["faturamento"], mapping["custo_liquido"],
        faturamento_minimo=limiar_relevancia,
    )
    if prop.empty:
        return []

    pior = prop.iloc[0]
    pct = pior["percentual_sobre_faturamento"]
    col_marca = mapping["marca"]

    if pct < 80:
        texto = (
            f"Nenhuma marca relevante apresenta Custo Líquido desproporcional ao "
            f"faturamento — a maior proporção encontrada é de {pior[col_marca]} "
            f"({pct:.1f}% do faturamento), dentro de uma faixa saudável."
        )
        return [{"titulo": "Custo Líquido em Proporção ao Faturamento", "texto": texto, "nivel": "positivo"}]

    texto = (
        f"{pior[col_marca]} tem o Custo Líquido mais desproporcional ao faturamento "
        f"entre as marcas relevantes: {pct:.1f}% do faturamento vira custo"
    )
    if pct >= 100:
        texto += (
            " — ou seja, essa marca opera no prejuízo mesmo antes de considerar "
            "despesas adicionais. Diferente de simplesmente vender pouco, aqui o "
            "problema é estrutural: o custo não está coberto pelo preço praticado. "
            "Priorize revisão de preço ou renegociação de custo com o fornecedor."
        )
        nivel = "critico"
    else:
        texto += (
            ", uma margem de manobra estreita — qualquer aumento de custo do "
            "fornecedor sem repasse de preço já reduz a rentabilidade dessa marca "
            "a praticamente zero. Vale monitorar de perto."
        )
        nivel = "alerta"

    zona_risco = prop[prop["percentual_sobre_faturamento"] >= 80]
    if len(zona_risco) > 1:
        outras = zona_risco.iloc[1:4][col_marca].tolist()
        if outras:
            texto += (
                f" Também na zona de risco (custo acima de 80% do faturamento): "
                f"{', '.join(str(x) for x in outras)}."
            )

    return [{"titulo": "Custo Líquido em Proporção ao Faturamento", "texto": texto, "nivel": nivel}]